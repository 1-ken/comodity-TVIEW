from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core import state

router = APIRouter()


@router.websocket("/ws/observe")
async def ws_observe(ws: WebSocket):
    """WebSocket endpoint for streaming real-time commodities data."""
    await ws.accept()

    if not state.observer:
        await ws.send_json({"error": "Observer not ready"})
        await ws.close()
        return

    state.active_websockets.add(ws)

    try:
        while True:
            try:
                await ws.receive_text()
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        state.active_websockets.discard(ws)
        try:
            await ws.close()
        except Exception:
            pass
