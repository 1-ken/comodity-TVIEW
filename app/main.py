import asyncio
import logging
import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.api.v1.endpoints.public import router as public_router
from app.api.v1.endpoints.stream import router as stream_router
from app.core import state
from app.core.config import CONFIG, STREAM_INTERVAL, SYMBOLS
from app.services.email_service import EmailService
from app.services.observer import SiteObserver
from app.services.sms_service import SMSService

# Configure logging with local time
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.Formatter.converter = time.localtime
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Commodities Observer",
    description="Real-time commodities price monitoring with price alerts",
    version="1.0.0",
)

# Configure CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],  # Allow all headers
)

app.include_router(public_router)
app.include_router(stream_router)
app.include_router(api_router, prefix="/api")


async def background_monitoring_task():
    """Background task that continuously monitors prices and checks alerts.
    Runs independently of WebSocket connections.
    Stores historical data for replay functionality.
    """
    logger.info("Background monitoring task started")

    while not state.shutdown_event.is_set():
        try:
            if not state.observer:
                logger.warning("Observer not ready, waiting...")
                await asyncio.sleep(STREAM_INTERVAL)
                continue

            # Get snapshot data
            data = await state.observer.snapshot(SYMBOLS)

            # Store in price history for replay functionality
            state.price_history.add_snapshot(data)

            # Check if we're in replay mode - if so, get next snapshot from replay
            if state.replay_manager.is_replaying():
                replayed_snapshot = state.replay_manager.get_next_snapshot()
                if replayed_snapshot:
                    data = replayed_snapshot.get("snapshot", data)
                else:
                    # Replay finished
                    logger.info("Replay finished")

            # Check price alerts
            triggered_alerts = state.alert_manager.check_alerts(data.get("pairs", []))
            if triggered_alerts:
                logger.info("Processing %s triggered alerts", len(triggered_alerts))
                for alert_data in triggered_alerts:
                    alert = alert_data["alert"]
                    current_price = alert_data["current_price"]
                    channels = alert.get("channels", [])

                    # Send via SMS if configured
                    if "sms" in channels and state.sms_service and alert.get("phone"):
                        try:
                            state.sms_service.send_price_alert(
                                to_phone=alert["phone"],
                                pair=alert["pair"],
                                target_price=alert["target_price"],
                                current_price=current_price,
                                condition=alert["condition"],
                                custom_message=alert.get("custom_message", ""),
                            )
                            logger.info("SMS alert sent for %s to %s", alert["pair"], alert["phone"])
                        except Exception as e:
                            logger.error("Failed to send SMS alert: %s", e)

                    # Send via Email if configured
                    if "email" in channels and state.email_service and alert.get("email"):
                        try:
                            state.email_service.send_price_alert(
                                to_email=alert["email"],
                                pair=alert["pair"],
                                target_price=alert["target_price"],
                                current_price=current_price,
                                condition=alert["condition"],
                                custom_message=alert.get("custom_message", ""),
                            )
                            logger.info("Email alert sent for %s to %s", alert["pair"], alert["email"])
                        except Exception as e:
                            logger.error("Failed to send email alert: %s", e)

            # Include alerts in data for WebSocket clients
            data["alerts"] = {
                "active": [a.to_dict() for a in state.alert_manager.get_active_alerts()],
                "triggered": [a.to_dict() for a in state.alert_manager.get_all_alerts() if a.status == "triggered"],
            }

            # Broadcast to all connected WebSocket clients
            if state.active_websockets:
                disconnected = set()
                for ws in state.active_websockets:
                    try:
                        await ws.send_json(data)
                    except Exception:
                        disconnected.add(ws)

                # Remove disconnected clients
                state.active_websockets.difference_update(disconnected)
                if disconnected:
                    logger.info("Removed %s disconnected WebSocket clients", len(disconnected))

            # Wait for next interval
            await asyncio.sleep(STREAM_INTERVAL)

        except asyncio.CancelledError:
            logger.info("Background monitoring task cancelled")
            break
        except Exception as e:
            logger.error("Error in background monitoring task: %s", e)
            await asyncio.sleep(STREAM_INTERVAL)

    logger.info("Background monitoring task stopped")


@app.on_event("startup")
async def on_startup():
    """Initialize the observer on application startup."""
    logger.info("Starting Commodities Observer application...")

    state.shutdown_event.clear()

    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    if sendgrid_api_key:
        state.email_service = EmailService(sendgrid_api_key)
        logger.info("SendGrid email service initialized")
    else:
        logger.warning("SENDGRID_API_KEY not set, email alerts disabled")

    # Initialize SMS service if credentials available
    af_username = os.getenv("AFRICASTALKING_USERNAME")
    af_api_key = os.getenv("AFRICASTALKING_API_KEY")
    if af_username and af_api_key:
        try:
            state.sms_service = SMSService(af_username, af_api_key)
            logger.info("Africa's Talking SMS service initialized")
        except Exception as e:
            logger.error("Failed to initialize SMS service: %s", e)
    else:
        logger.warning("AFRICASTALKING credentials not set, SMS alerts disabled")

    try:
        state.observer = SiteObserver(
            url=CONFIG.get("url"),
            table_selector=CONFIG.get("tableSelector"),
            pair_cell_selector=CONFIG.get("pairCellSelector"),
            wait_selector=CONFIG.get("waitSelector", "body"),
            inject_mutation_observer=bool(CONFIG.get("injectMutationObserver", True)),
            price_column_index=CONFIG.get("priceIndex", 3),
        )
        await state.observer.startup()
        logger.info("Commodities observer started successfully")

        # Start background monitoring task
        state.background_task = asyncio.create_task(background_monitoring_task())
        logger.info("Background monitoring task created")

    except Exception as e:
        logger.error("Failed to start observer: %s", e)
        raise


@app.on_event("shutdown")
async def on_shutdown():
    """Clean up resources on application shutdown."""
    # Stop background task
    logger.info("Stopping background monitoring task...")
    state.shutdown_event.set()
    if state.background_task:
        state.background_task.cancel()
        try:
            await state.background_task
        except asyncio.CancelledError:
            pass
        logger.info("Background monitoring task stopped")

    # Shutdown observer
    if state.observer:
        logger.info("Shutting down observer...")
        try:
            await state.observer.shutdown()
            logger.info("Observer shutdown complete")
        except Exception as e:
            logger.error("Error during shutdown: %s", e)
