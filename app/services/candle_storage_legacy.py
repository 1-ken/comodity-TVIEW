"""
Candle storage and management for multiple timeframes.
Persists OHLC candles to disk and provides retrieval functions.
"""
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from app.core.paths import CANDLES_PATHS

logger = logging.getLogger(__name__)


class CandleStorage:
    """Manages candle persistence and retrieval for all timeframes."""

    def __init__(self):
        self.candles: Dict[str, List[Dict[str, Any]]] = {tf: [] for tf in CANDLES_PATHS}
        self._load_all_candles()

    def _load_all_candles(self) -> None:
        """Load candles for all timeframes from disk."""
        for timeframe, path in CANDLES_PATHS.items():
            try:
                if Path(path).exists():
                    with open(path, "r") as f:
                        self.candles[timeframe] = json.load(f)
                    logger.info(
                        "Loaded %s candles for timeframe %s",
                        len(self.candles[timeframe]),
                        timeframe,
                    )
                else:
                    self.candles[timeframe] = []
            except Exception as e:
                logger.error("Error loading candles for %s: %s", timeframe, e)
                self.candles[timeframe] = []

    def _save_candles(self, timeframe: str) -> None:
        """Save candles for a specific timeframe to disk."""
        try:
            path = CANDLES_PATHS.get(timeframe)
            if path:
                with open(path, "w") as f:
                    json.dump(self.candles[timeframe], f, indent=2)
        except Exception as e:
            logger.error("Error saving candles for %s: %s", timeframe, e)

    def add_candle(self, timeframe: str, candle: Dict[str, Any]) -> None:
        """Add a candle to a timeframe."""
        if timeframe in self.candles:
            self.candles[timeframe].append(candle)
            self._save_candles(timeframe)

    def add_candles_batch(self, timeframe: str, candles: List[Dict[str, Any]]) -> None:
        """Add multiple candles to a timeframe."""
        if timeframe in self.candles:
            self.candles[timeframe].extend(candles)
            self._save_candles(timeframe)

    def get_candles(self, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get latest N candles for a timeframe."""
        if timeframe in self.candles:
            return self.candles[timeframe][-limit:]
        return []

    def get_all_candles(self, timeframe: str) -> List[Dict[str, Any]]:
        """Get all candles for a timeframe."""
        if timeframe in self.candles:
            return self.candles[timeframe]
        return []

    def get_candles_by_date(
        self, timeframe: str, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Get candles within a date range for a timeframe."""
        if timeframe not in self.candles:
            return []

        result = []
        try:
            from datetime import datetime

            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)

            for candle in self.candles[timeframe]:
                candle_time = datetime.fromisoformat(candle["timestamp"])
                if start <= candle_time <= end:
                    result.append(candle)
        except ValueError as e:
            logger.error("Invalid date format: %s", e)

        return result

    def get_latest_candle(self, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get the most recent candle for a timeframe."""
        if timeframe in self.candles and self.candles[timeframe]:
            return self.candles[timeframe][-1]
        return None

    def get_stats(self) -> Dict[str, int]:
        """Get candle counts for all timeframes."""
        return {tf: len(candles) for tf, candles in self.candles.items()}

    def clear_timeframe(self, timeframe: str) -> None:
        """Clear all candles for a timeframe."""
        if timeframe in self.candles:
            self.candles[timeframe] = []
            self._save_candles(timeframe)
            logger.info("Cleared candles for %s", timeframe)
