"""
OHLC candle aggregator for multiple timeframes.
Aggregates 1-second price snapshots into 1m, 5m, 15m, 30m, 1h, 4h, daily, and 3-day candles.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# Timeframe definitions in seconds
TIMEFRAMES = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "4h": 14400,
    "daily": 86400,
    "3d": 259200,
}


class CandleAggregator:
    """Aggregates price snapshots into OHLC candles for multiple timeframes."""

    def __init__(self):
        self.candles: Dict[str, List[Dict[str, Any]]] = {tf: [] for tf in TIMEFRAMES}

    def aggregate_snapshots(
        self, snapshots: List[Dict[str, Any]], pair: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregate snapshots into candles for all timeframes.
        
        Args:
            snapshots: List of price snapshots with timestamp and price data
            pair: Trading pair (e.g., "AAPL", "SPX")
            
        Returns:
            Dict mapping timeframe to list of candles
        """
        result = {tf: [] for tf in TIMEFRAMES}

        # Group snapshots by pair if it's in the snapshot
        pair_snapshots = []
        for snap in snapshots:
            snapshot_data = snap.get("snapshot", {})
            pairs = snapshot_data.get("pairs", [])

            # Find the pair in this snapshot
            for p in pairs:
                if p.get("pair") == pair:
                    pair_snapshots.append(
                        {
                            "timestamp": snap.get("timestamp"),
                            "price": p.get("price"),
                        }
                    )
                    break

        # Aggregate into each timeframe
        for timeframe, seconds in TIMEFRAMES.items():
            result[timeframe] = self._aggregate_to_timeframe(
                pair_snapshots, timeframe, seconds
            )

        return result

    @staticmethod
    def _aggregate_to_timeframe(
        snapshots: List[Dict[str, Any]], timeframe: str, seconds: int
    ) -> List[Dict[str, Any]]:
        """Aggregate snapshots into candles for a specific timeframe."""
        if not snapshots:
            return []

        candles = []
        grouped = defaultdict(list)

        # Group snapshots by candle period
        for snap in snapshots:
            try:
                ts = datetime.fromisoformat(snap["timestamp"].replace("Z", "+00:00"))
                # Calculate candle start time
                candle_start = (ts.timestamp() // seconds) * seconds
                grouped[int(candle_start)].append(snap)
            except (ValueError, TypeError):
                logger.warning("Invalid timestamp: %s", snap.get("timestamp"))
                continue

        # Build candles from groups
        for candle_time in sorted(grouped.keys()):
            prices = []
            for snap in grouped[candle_time]:
                try:
                    # Handle price as string (e.g., "260.62") or number
                    price_str = str(snap.get("price", "0")).replace(",", "")
                    price = float(price_str) if price_str else 0.0
                    if price > 0:  # Filter out invalid prices
                        prices.append(price)
                except (ValueError, TypeError):
                    continue

            if prices:
                candle = {
                    "timestamp": datetime.fromtimestamp(candle_time).isoformat(),
                    "open": prices[0],
                    "high": max(prices),
                    "low": min(prices),
                    "close": prices[-1],
                    "volume": len(prices),  # Number of ticks in candle
                    "timeframe": timeframe,
                }
                candles.append(candle)

        return candles

    @staticmethod
    def get_latest_candle(candles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get the most recent candle."""
        return candles[-1] if candles else None

    @staticmethod
    def get_candles_range(
        candles: List[Dict[str, Any]], limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get last N candles."""
        return candles[-limit:] if candles else []

    @staticmethod
    def get_candles_by_date(
        candles: List[Dict[str, Any]],
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """Get candles within a date range."""
        result = []
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)

            for candle in candles:
                candle_time = datetime.fromisoformat(candle["timestamp"])
                if start <= candle_time <= end:
                    result.append(candle)
        except ValueError as e:
            logger.error("Invalid date format: %s", e)

        return result
