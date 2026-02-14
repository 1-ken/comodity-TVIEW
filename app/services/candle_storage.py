"""
Candle storage and management for multiple timeframes - PostgreSQL version.
Persists OHLC candles to database.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.models import Candle as CandleModel

logger = logging.getLogger(__name__)

TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "daily", "3d"]


class CandleStorage:
    """Manages candle persistence and retrieval in PostgreSQL using session-per-operation pattern."""

    def __init__(self):
        """Initialize candle storage manager. No persistent session or in-memory cache."""
        pass

    @contextmanager
    def _get_session(self):
        """Context manager for database sessions with automatic cleanup and rollback on error."""
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error("Database error, rolled back transaction: %s", e)
            raise
        finally:
            db.close()

    def add_candle(self, timeframe: str, candle: Dict[str, Any]) -> None:
        """Add a candle to a timeframe."""
        if timeframe not in TIMEFRAMES:
            logger.warning("Unknown timeframe: %s", timeframe)
            return

        with self._get_session() as db:
            timestamp = candle.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.utcnow()

            db_candle = CandleModel(
                pair=candle.get("pair", ""),
                timeframe=timeframe,
                timestamp=timestamp,
                open=candle.get("open", 0),
                high=candle.get("high", 0),
                low=candle.get("low", 0),
                close=candle.get("close", 0),
                volume=candle.get("volume", 0),
            )
            db.add(db_candle)

    def add_candles_batch(self, timeframe: str, candles: List[Dict[str, Any]]) -> None:
        """Add multiple candles to a timeframe."""
        if timeframe not in TIMEFRAMES:
            logger.warning("Unknown timeframe: %s", timeframe)
            return

        with self._get_session() as db:
            for candle in candles:
                timestamp = candle.get("timestamp")
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                elif not isinstance(timestamp, datetime):
                    timestamp = datetime.utcnow()

                db_candle = CandleModel(
                    pair=candle.get("pair", ""),
                    timeframe=timeframe,
                    timestamp=timestamp,
                    open=candle.get("open", 0),
                    high=candle.get("high", 0),
                    low=candle.get("low", 0),
                    close=candle.get("close", 0),
                    volume=candle.get("volume", 0),
                )
                db.add(db_candle)
            logger.debug("Added batch of %d candles for %s", len(candles), timeframe)

    def get_candles(self, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get latest N candles for a timeframe."""
        if timeframe not in TIMEFRAMES:
            return []

        with self._get_session() as db:
            records = (
                db.query(CandleModel)
                .filter(CandleModel.timeframe == timeframe)
                .order_by(CandleModel.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [self._to_dict(r) for r in reversed(records)]

    def get_all_candles(self, timeframe: str) -> List[Dict[str, Any]]:
        """Get all candles for a timeframe."""
        if timeframe not in TIMEFRAMES:
            return []

        with self._get_session() as db:
            records = (
                db.query(CandleModel)
                .filter(CandleModel.timeframe == timeframe)
                .order_by(CandleModel.timestamp)
                .all()
            )
            return [self._to_dict(r) for r in records]

    def get_candles_by_date(
        self, timeframe: str, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Get candles within a date range for a timeframe."""
        if timeframe not in TIMEFRAMES:
            return []

        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)

            with self._get_session() as db:
                records = (
                    db.query(CandleModel)
                    .filter(
                        and_(
                            CandleModel.timeframe == timeframe,
                            CandleModel.timestamp >= start_dt,
                            CandleModel.timestamp <= end_dt,
                        )
                    )
                    .order_by(CandleModel.timestamp)
                    .all()
                )
                return [self._to_dict(r) for r in records]
        except ValueError as e:
            logger.error("Invalid date format: %s", e)
            return []

    def get_latest_candle(self, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get the most recent candle for a timeframe."""
        if timeframe not in TIMEFRAMES:
            return None

        with self._get_session() as db:
            record = (
                db.query(CandleModel)
                .filter(CandleModel.timeframe == timeframe)
                .order_by(CandleModel.timestamp.desc())
                .first()
            )
            return self._to_dict(record) if record else None

    def get_candles_for_pair(
        self, pair: str, timeframe: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get candles for a specific pair and timeframe."""
        if timeframe not in TIMEFRAMES:
            return []

        with self._get_session() as db:
            records = (
                db.query(CandleModel)
                .filter(
                    and_(
                        CandleModel.pair == pair,
                        CandleModel.timeframe == timeframe,
                    )
                )
                .order_by(CandleModel.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [self._to_dict(r) for r in reversed(records)]

    @staticmethod
    def _to_dict(record: CandleModel) -> Dict[str, Any]:
        """Convert ORM model to dictionary."""
        if not record:
            return None
        return {
            "id": record.id,
            "pair": record.pair,
            "timeframe": record.timeframe,
            "timestamp": record.timestamp.isoformat() if record.timestamp else None,
            "open": record.open,
            "high": record.high,
            "low": record.low,
            "close": record.close,
            "volume": record.volume,
        }
