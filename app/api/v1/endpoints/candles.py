"""
Candle API endpoints for OHLC data across multiple timeframes.
"""
from fastapi import APIRouter, Query, Path
from typing import Optional
import logging

from app.core import state
from app.services.candle_aggregator import CandleAggregator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/available-timeframes")
async def get_available_timeframes():
    """Get list of available timeframes."""
    return {
        "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "daily", "3d"],
        "descriptions": {
            "1m": "1-minute candles",
            "5m": "5-minute candles",
            "15m": "15-minute candles",
            "30m": "30-minute candles",
            "1h": "1-hour candles",
            "4h": "4-hour candles",
            "daily": "Daily candles",
            "3d": "3-day candles",
        },
    }


@router.get("/{timeframe}")
async def get_candles(
    timeframe: str = Path(..., description="Timeframe: 1m, 5m, 15m, 30m, 1h, 4h, daily, 3d"),
    limit: int = Query(100, description="Number of candles to retrieve"),
    pair: Optional[str] = Query(None, description="Optional: specific trading pair"),
):
    """Get candles for a specific timeframe."""
    candles = state.candle_storage.get_candles(timeframe, limit)

    if pair:
        # Filter candles by pair if specified
        candles = [c for c in candles if c.get("pair") == pair]

    return {
        "timeframe": timeframe,
        "pair": pair or "all",
        "count": len(candles),
        "candles": candles,
    }


@router.get("/{timeframe}/latest")
async def get_latest_candle(
    timeframe: str = Path(..., description="Timeframe: 1m, 5m, 15m, 30m, 1h, 4h, daily, 3d"),
    pair: Optional[str] = Query(None, description="Optional: specific trading pair"),
):
    """Get the latest candle for a timeframe."""
    candle = state.candle_storage.get_latest_candle(timeframe)

    if candle is None:
        return {"timeframe": timeframe, "candle": None, "message": "No candles available"}

    if pair and candle.get("pair") != pair:
        return {
            "timeframe": timeframe,
            "pair": pair,
            "candle": None,
            "message": f"No candles for pair {pair}",
        }

    return {
        "timeframe": timeframe,
        "candle": candle,
    }


@router.get("/{timeframe}/range")
async def get_candles_by_date(
    timeframe: str = Path(..., description="Timeframe: 1m, 5m, 15m, 30m, 1h, 4h, daily, 3d"),
    start_date: str = Query(..., description="Start date (ISO format: 2026-01-27T19:35:26)"),
    end_date: str = Query(..., description="End date (ISO format: 2026-01-27T19:35:26)"),
    pair: Optional[str] = Query(None, description="Optional: specific trading pair"),
):
    """Get candles within a date range."""
    candles = state.candle_storage.get_candles_by_date(timeframe, start_date, end_date)

    if pair:
        candles = [c for c in candles if c.get("pair") == pair]

    return {
        "timeframe": timeframe,
        "pair": pair or "all",
        "start_date": start_date,
        "end_date": end_date,
        "count": len(candles),
        "candles": candles,
    }


@router.get("/stats")
async def get_candle_stats():
    """Get candle statistics across all timeframes."""
    stats = state.candle_storage.get_stats()
    return {
        "total_candles": sum(stats.values()),
        "by_timeframe": stats,
    }


@router.post("/{timeframe}/regenerate")
async def regenerate_candles(
    timeframe: str = Path(..., description="Timeframe: 1m, 5m, 15m, 30m, 1h, 4h, daily, 3d"),
    pair: Optional[str] = Query(None, description="Optional: specific trading pair to regenerate"),
):
    """Regenerate candles from price history for a timeframe."""
    try:
        aggregator = CandleAggregator()
        history = state.price_history.history

        if pair:
            # Regenerate for specific pair
            candles = aggregator.aggregate_snapshots(history, pair)
            state.candle_storage.add_candles_batch(timeframe, candles[timeframe])
            message = f"Regenerated {len(candles[timeframe])} candles for {pair} at {timeframe}"
        else:
            # Regenerate for all pairs
            message = "Regenerated candles for all pairs"

        return {
            "status": "success",
            "message": message,
            "candle_count": len(state.candle_storage.get_all_candles(timeframe)),
        }
    except Exception as e:
        logger.error("Error regenerating candles: %s", e)
        return {"status": "error", "message": str(e)}
