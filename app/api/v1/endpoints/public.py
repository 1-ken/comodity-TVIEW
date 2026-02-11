import os

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from app.core import state
from app.core.config import SYMBOLS
from app.core.paths import CLIENT_HTML_PATH

router = APIRouter()


@router.get("/")
async def root():
    """Serve the client HTML page."""
    return FileResponse(CLIENT_HTML_PATH)


@router.get("/client-config")
async def client_config():
    """Serve client runtime configuration derived from environment."""
    ws_url = os.getenv("WS_URL", "ws://localhost:8001/ws/observe")
    return JSONResponse({
        "wsUrl": ws_url,
    })


@router.get("/snapshot")
async def snapshot():
    """Get a single snapshot of current commodities data."""
    if not state.observer:
        return JSONResponse({"error": "Observer not ready"}, status_code=503)

    try:
        data = await state.observer.snapshot(SYMBOLS)
        return JSONResponse(data)
    except Exception:
        return JSONResponse({"error": "Failed to get snapshot"}, status_code=500)
