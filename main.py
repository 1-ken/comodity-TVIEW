import asyncio
import json
import logging
import os
import time
import certifi
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from observer import SiteObserver
from alerts import AlertManager, Alert
from email_service import EmailService
from sms_service import SMSService
from price_history import PriceHistory
from replay_manager import ReplayManager

# Load environment variables from .env file
load_dotenv()

# Configure logging with local time
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.Formatter.converter = time.localtime
logger = logging.getLogger(__name__)

HERE = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(HERE, "config.json")

# Load configuration
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CONFIG: Dict[str, Any] = json.load(f)
except FileNotFoundError:
    logger.error(f"Config file not found: {CONFIG_PATH}")
    raise
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in config file: {e}")
    raise

STREAM_INTERVAL = float(CONFIG.get("streamIntervalSeconds", 1))
SYMBOLS = CONFIG.get("symbols", [])

# Initialize alert manager and email service
alert_manager = AlertManager()
email_service = None
sms_service = None
sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
if sendgrid_api_key:
    email_service = EmailService(sendgrid_api_key)
    logger.info("SendGrid email service initialized")
else:
    logger.warning("SENDGRID_API_KEY not set, email alerts disabled")

# Initialize SMS service if credentials available
af_username = os.getenv("AFRICASTALKING_USERNAME")
af_api_key = os.getenv("AFRICASTALKING_API_KEY")
if af_username and af_api_key:
    try:
        sms_service = SMSService(af_username, af_api_key)
        logger.info("Africa's Talking SMS service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize SMS service: {e}")
else:
    logger.warning("AFRICASTALKING credentials not set, SMS alerts disabled")

app = FastAPI(
    title="Commodities Observer",
    description="Real-time commodities price monitoring with price alerts",
    version="1.0.0"
)

observer: SiteObserver | None = None
active_websockets: set[WebSocket] = set()
background_task: asyncio.Task | None = None
shutdown_event = asyncio.Event()

# Price history and replay
price_history = PriceHistory()
replay_manager = ReplayManager()


async def background_monitoring_task():
    """Background task that continuously monitors prices and checks alerts.
    Runs independently of WebSocket connections.
    Stores historical data for replay functionality.
    """
    logger.info("Background monitoring task started")
    
    while not shutdown_event.is_set():
        try:
            if not observer:
                logger.warning("Observer not ready, waiting...")
                await asyncio.sleep(STREAM_INTERVAL)
                continue
            
            # Get snapshot data
            data = await observer.snapshot(SYMBOLS)
            
            # Store in price history for replay functionality
            price_history.add_snapshot(data)
            
            # Check if we're in replay mode - if so, get next snapshot from replay
            if replay_manager.is_replaying():
                replayed_snapshot = replay_manager.get_next_snapshot()
                if replayed_snapshot:
                    data = replayed_snapshot.get("snapshot", data)
                else:
                    # Replay finished
                    logger.info("Replay finished")
            
            # Check price alerts
            triggered_alerts = alert_manager.check_alerts(data.get("pairs", []))
            if triggered_alerts:
                logger.info(f"Processing {len(triggered_alerts)} triggered alerts")
                for alert_data in triggered_alerts:
                    alert = alert_data["alert"]
                    current_price = alert_data["current_price"]
                    channels = alert.get("channels", [])
                    
                    # Send via SMS if configured
                    if "sms" in channels and sms_service and alert.get("phone"):
                        try:
                            sms_service.send_price_alert(
                                to_phone=alert["phone"],
                                pair=alert["pair"],
                                target_price=alert["target_price"],
                                current_price=current_price,
                                condition=alert["condition"],
                                custom_message=alert.get("custom_message", ""),
                            )
                            logger.info(f"SMS alert sent for {alert['pair']} to {alert['phone']}")
                        except Exception as e:
                            logger.error(f"Failed to send SMS alert: {e}")
                    
                    # Send via Email if configured
                    if "email" in channels and email_service and alert.get("email"):
                        try:
                            email_service.send_price_alert(
                                to_email=alert["email"],
                                pair=alert["pair"],
                                target_price=alert["target_price"],
                                current_price=current_price,
                                condition=alert["condition"],
                                custom_message=alert.get("custom_message", ""),
                            )
                            logger.info(f"Email alert sent for {alert['pair']} to {alert['email']}")
                        except Exception as e:
                            logger.error(f"Failed to send email alert: {e}")
            
            # Include alerts in data for WebSocket clients
            data["alerts"] = {
                "active": [a.to_dict() for a in alert_manager.get_active_alerts()],
                "triggered": [a.to_dict() for a in alert_manager.get_all_alerts() if a.status == "triggered"],
            }
            
            # Broadcast to all connected WebSocket clients
            if active_websockets:
                disconnected = set()
                for ws in active_websockets:
                    try:
                        await ws.send_json(data)
                    except Exception as e:
                        logger.debug(f"Failed to send to WebSocket client: {e}")
                        disconnected.add(ws)
                
                # Remove disconnected clients
                active_websockets.difference_update(disconnected)
                if disconnected:
                    logger.info(f"Removed {len(disconnected)} disconnected WebSocket clients")
            
            # Wait for next interval
            await asyncio.sleep(STREAM_INTERVAL)
            
        except asyncio.CancelledError:
            logger.info("Background monitoring task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in background monitoring task: {e}")
            await asyncio.sleep(STREAM_INTERVAL)
    
    logger.info("Background monitoring task stopped")


@app.on_event("startup")
async def on_startup():
    """Initialize the observer on application startup."""
    global observer, background_task
    logger.info("Starting Commodities Observer application...")
    
    try:
        observer = SiteObserver(
            url=CONFIG.get("url"),
            table_selector=CONFIG.get("tableSelector"),
            pair_cell_selector=CONFIG.get("pairCellSelector"),
            wait_selector=CONFIG.get("waitSelector", "body"),
            inject_mutation_observer=bool(CONFIG.get("injectMutationObserver", True)),
            price_column_index=CONFIG.get("priceIndex", 3),
        )
        await observer.startup()
        logger.info("Commodities observer started successfully")
        
        # Start background monitoring task
        background_task = asyncio.create_task(background_monitoring_task())
        logger.info("Background monitoring task created")
        
    except Exception as e:
        logger.error(f"Failed to start observer: {e}")
        raise


@app.on_event("shutdown")
async def on_shutdown():
    """Clean up resources on application shutdown."""
    global background_task
    
    # Stop background task
    logger.info("Stopping background monitoring task...")
    shutdown_event.set()
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass
        logger.info("Background monitoring task stopped")
    
    # Shutdown observer
    if observer:
        logger.info("Shutting down observer...")
        try:
            await observer.shutdown()
            logger.info("Observer shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


@app.get("/")
async def root():
    """Serve the client HTML page."""
    return FileResponse(os.path.join(HERE, "client.html"))


@app.get("/client-config")
async def client_config():
    """Serve client runtime configuration derived from environment.
    Allows overriding WebSocket URLs when running behind proxies or differing hosts.
    """
    ws_url = os.getenv("WS_URL", "ws://localhost:8001/ws/observe")
    return JSONResponse({
        "wsUrl": ws_url,
    })


@app.get("/snapshot")
async def snapshot():
    """Get a single snapshot of current commodities data."""
    if not observer:
        logger.warning("Snapshot requested but observer not ready")
        return JSONResponse({"error": "Observer not ready"}, status_code=503)
    
    try:
        data = await observer.snapshot(SYMBOLS)
        return JSONResponse(data)
    except Exception as e:
        logger.error(f"Error getting snapshot: {e}")
        return JSONResponse({"error": "Failed to get snapshot"}, status_code=500)


@app.websocket("/ws/observe")
async def ws_observe(ws: WebSocket):
    """WebSocket endpoint for streaming real-time commodities data.
    Clients receive broadcasts from the background monitoring task.
    """
    await ws.accept()
    logger.info(f"WebSocket connection established: {ws.client}")
    
    if not observer:
        logger.warning("WebSocket connection but observer not ready")
        await ws.send_json({"error": "Observer not ready"})
        await ws.close()
        return

    # Register this WebSocket client
    active_websockets.add(ws)
    logger.info(f"Active WebSocket clients: {len(active_websockets)}")
    
    try:
        # Keep connection alive and wait for disconnect
        while True:
            # Just wait for messages from client (or disconnect)
            # The background task handles broadcasting data
            try:
                await ws.receive_text()
            except WebSocketDisconnect:
                break
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed: {ws.client}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Unregister this WebSocket client
        active_websockets.discard(ws)
        logger.info(f"WebSocket client removed. Active clients: {len(active_websockets)}")
        try:
            await ws.close()
        except Exception:
            pass


# Replay API Endpoints

@app.get("/api/replay/info")
async def replay_info():
    """Get information about available price history for replay."""
    date_range = price_history.get_date_range()
    return {
        "total_snapshots": price_history.get_snapshot_count(),
        "date_range": date_range,
        "status": replay_manager.get_status(),
    }


@app.post("/api/replay/start")
async def start_replay(
    start_index: int = 0,
    speed: float = 1.0,
):
    """Start price replay from a specific snapshot index."""
    snapshots = price_history.get_history_range()
    
    if not snapshots:
        raise HTTPException(status_code=400, detail="No price history available")
    
    if not (0 <= start_index < len(snapshots)):
        raise HTTPException(status_code=400, detail=f"Invalid start_index. Must be 0-{len(snapshots)-1}")
    
    if not (0.25 <= speed <= 4.0):
        raise HTTPException(status_code=400, detail="Speed must be between 0.25 and 4.0")
    
    status = replay_manager.start_replay(snapshots, start_index=start_index, speed=speed)
    logger.info(f"Started replay: {snapshots}")
    return status


@app.post("/api/replay/pause")
async def pause_replay():
    """Pause the current replay."""
    return replay_manager.pause()


@app.post("/api/replay/resume")
async def resume_replay():
    """Resume the paused replay."""
    return replay_manager.resume()


@app.post("/api/replay/stop")
async def stop_replay():
    """Stop replay completely."""
    return replay_manager.stop()


@app.post("/api/replay/speed")
async def set_replay_speed(speed: float):
    """Set replay speed (0.25x to 4x)."""
    if not (0.25 <= speed <= 4.0):
        raise HTTPException(status_code=400, detail="Speed must be between 0.25 and 4.0")
    return replay_manager.set_speed(speed)


@app.post("/api/replay/seek")
async def seek_replay(index: int = 0):
    """Seek to specific snapshot index."""
    if not (0 <= index < price_history.get_snapshot_count()):
        raise HTTPException(status_code=400, detail=f"Invalid index. Must be 0-{price_history.get_snapshot_count()-1}")
    return replay_manager.seek_to_index(index)


@app.post("/api/replay/seek-percent")
async def seek_replay_percent(percent: float):
    """Seek to percentage of replay (0-100)."""
    if not (0 <= percent <= 100):
        raise HTTPException(status_code=400, detail="Percentage must be between 0 and 100")
    return replay_manager.seek_to_percentage(percent)


@app.get("/api/replay/status")
async def get_replay_status():
    """Get current replay status."""
    return replay_manager.get_status()


@app.get("/api/replay/history")
async def get_price_history(limit: int = 100):
    """Get recent price history snapshots."""
    all_history = price_history.get_history_range()
    # Return the last 'limit' snapshots
    return {
        "total": len(all_history),
        "returned": len(all_history[-limit:]),
        "history": all_history[-limit:],
    }


# Alert API Endpoints

class CreateAlertRequest(BaseModel):
    pair: str
    target_price: float
    condition: str  # "above", "below", or "equal"
    channels: List[str] = ["email"]  # ["email"], ["sms"], or ["email", "sms"]
    email: str = ""
    phone: str = ""
    custom_message: str = ""  # Optional custom message for the alert


@app.post("/api/alerts")
async def create_alert(request: CreateAlertRequest):
    """Create a new price alert."""
    if request.condition not in ["above", "below", "equal"]:
        raise HTTPException(status_code=400, detail="Condition must be 'above', 'below', or 'equal'")
    
    if not request.channels:
        raise HTTPException(status_code=400, detail="At least one channel (email or sms) must be selected")
    
    invalid_channels = set(request.channels) - {"email", "sms"}
    if invalid_channels:
        raise HTTPException(status_code=400, detail=f"Invalid channels: {invalid_channels}. Must be 'email' or 'sms'")
    
    if "email" in request.channels and not request.email:
        raise HTTPException(status_code=400, detail="Email is required for email alerts")
    if "sms" in request.channels and not request.phone:
        raise HTTPException(status_code=400, detail="Phone is required for SMS alerts")

    alert = alert_manager.create_alert(
        pair=request.pair,
        target_price=request.target_price,
        condition=request.condition,
        email=request.email,
        channels=request.channels,
        phone=request.phone,
        custom_message=request.custom_message,
    )
    return {"success": True, "alert": alert.to_dict()}


@app.get("/api/alerts")
async def get_alerts():
    """Get all alerts."""
    all_alerts = alert_manager.get_all_alerts()
    return {
        "total": len(all_alerts),
        "active": [a.to_dict() for a in all_alerts if a.status == "active"],
        "triggered": [a.to_dict() for a in all_alerts if a.status == "triggered"],
        "all": [a.to_dict() for a in all_alerts],
    }


@app.get("/api/alerts/{alert_id}")
async def get_alert(alert_id: str):
    """Get specific alert."""
    alert = alert_manager.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert.to_dict()


@app.delete("/api/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert."""
    if alert_manager.delete_alert(alert_id):
        return {"success": True, "message": "Alert deleted"}
    raise HTTPException(status_code=404, detail="Alert not found")
