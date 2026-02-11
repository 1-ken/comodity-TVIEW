from fastapi import APIRouter, HTTPException

from app.core import state

router = APIRouter()


@router.get("/info")
async def replay_info():
    """Get information about available price history for replay."""
    date_range = state.price_history.get_date_range()
    return {
        "total_snapshots": state.price_history.get_snapshot_count(),
        "date_range": date_range,
        "status": state.replay_manager.get_status(),
    }


@router.post("/start")
async def start_replay(
    start_index: int = 0,
    speed: float = 1.0,
):
    """Start price replay from a specific snapshot index."""
    snapshots = state.price_history.get_history_range()

    if not snapshots:
        raise HTTPException(status_code=400, detail="No price history available")

    if not (0 <= start_index < len(snapshots)):
        raise HTTPException(status_code=400, detail=f"Invalid start_index. Must be 0-{len(snapshots)-1}")

    if not (0.25 <= speed <= 4.0):
        raise HTTPException(status_code=400, detail="Speed must be between 0.25 and 4.0")

    status = state.replay_manager.start_replay(snapshots, start_index=start_index, speed=speed)
    return status


@router.post("/pause")
async def pause_replay():
    """Pause the current replay."""
    return state.replay_manager.pause()


@router.post("/resume")
async def resume_replay():
    """Resume the paused replay."""
    return state.replay_manager.resume()


@router.post("/stop")
async def stop_replay():
    """Stop replay completely."""
    return state.replay_manager.stop()


@router.post("/speed")
async def set_replay_speed(speed: float):
    """Set replay speed (0.25x to 4x)."""
    if not (0.25 <= speed <= 4.0):
        raise HTTPException(status_code=400, detail="Speed must be between 0.25 and 4.0")
    return state.replay_manager.set_speed(speed)


@router.post("/seek")
async def seek_replay(index: int = 0):
    """Seek to specific snapshot index."""
    if not (0 <= index < state.price_history.get_snapshot_count()):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid index. Must be 0-{state.price_history.get_snapshot_count()-1}",
        )
    return state.replay_manager.seek_to_index(index)


@router.post("/seek-percent")
async def seek_replay_percent(percent: float):
    """Seek to percentage of replay (0-100)."""
    if not (0 <= percent <= 100):
        raise HTTPException(status_code=400, detail="Percentage must be between 0 and 100")
    return state.replay_manager.seek_to_percentage(percent)


@router.get("/status")
async def get_replay_status():
    """Get current replay status."""
    return state.replay_manager.get_status()


@router.get("/history")
async def get_price_history(limit: int = 100):
    """Get recent price history snapshots."""
    all_history = state.price_history.get_history_range()
    return {
        "total": len(all_history),
        "returned": len(all_history[-limit:]),
        "history": all_history[-limit:],
    }
