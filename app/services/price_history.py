"""
Price history storage and management for replay functionality - PostgreSQL version.
Stores price snapshots with timestamps in database.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.models import PriceHistory as PriceHistoryModel

logger = logging.getLogger(__name__)


class PriceHistory:
    """Manages historical price data for replay in PostgreSQL using session-per-operation pattern."""

    def __init__(self):
        """Initialize price history manager. No persistent session stored."""
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

    @property
    def history(self) -> List[Dict[str, Any]]:
        """Get all historical snapshots for compatibility."""
        with self._get_session() as db:
            records = db.query(PriceHistoryModel).order_by(PriceHistoryModel.timestamp).all()
            return [self._to_dict(r) for r in records]

    def add_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Add a price snapshot with timestamp."""
        with self._get_session() as db:
            timestamp = snapshot.get("ts")
            if not timestamp:
                timestamp = datetime.utcnow().isoformat()
            elif isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except (ValueError, TypeError):
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()

            # Remove 'ts' field from snapshot data
            snapshot_copy = {k: v for k, v in snapshot.items() if k != "ts"}

            historical_entry = PriceHistoryModel(
                timestamp=timestamp,
                snapshot=snapshot_copy,
            )
            db.add(historical_entry)
            logger.debug("Added price history snapshot at %s", timestamp)

    def get_history_range(
        self, start_time: Optional[str] = None, end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get historical snapshots within a time range."""
        with self._get_session() as db:
            query = db.query(PriceHistoryModel)

            if start_time:
                try:
                    start_dt = datetime.fromisoformat(start_time)
                    query = query.filter(PriceHistoryModel.timestamp >= start_dt)
                except ValueError:
                    logger.warning("Invalid start_time format: %s", start_time)

            if end_time:
                try:
                    end_dt = datetime.fromisoformat(end_time)
                    query = query.filter(PriceHistoryModel.timestamp <= end_dt)
                except ValueError:
                    logger.warning("Invalid end_time format: %s", end_time)

            records = query.order_by(PriceHistoryModel.timestamp).all()
            return [self._to_dict(r) for r in records]

    def get_snapshot_at_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get snapshot at specific index."""
        with self._get_session() as db:
            records = db.query(PriceHistoryModel).order_by(PriceHistoryModel.timestamp).all()
            if 0 <= index < len(records):
                return self._to_dict(records[index])
            return None

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get the most recent snapshot."""
        with self._get_session() as db:
            record = (
                db.query(PriceHistoryModel)
                .order_by(PriceHistoryModel.timestamp.desc())
                .first()
            )
            return self._to_dict(record) if record else None

    def get_snapshot_count(self) -> int:
        """Get total number of snapshots."""
        with self._get_session() as db:
            return db.query(PriceHistoryModel).count()

    def clear_history(self) -> None:
        """Clear all history (use with caution)."""
        with self._get_session() as db:
            logger.warning("Clearing all price history")
            db.query(PriceHistoryModel).delete()

    def get_date_range(self) -> Optional[Dict[str, str]]:
        """Get earliest and latest timestamp in history."""
        with self._get_session() as db:
            records = (
                db.query(PriceHistoryModel)
                .order_by(PriceHistoryModel.timestamp)
                .all()
            )

            if not records:
                return None

            earliest = records[0].timestamp
            latest = records[-1].timestamp

            return {
                "earliest": earliest.isoformat() if earliest else None,
                "latest": latest.isoformat() if latest else None,
            }

    @staticmethod
    def _to_dict(record: PriceHistoryModel) -> Dict[str, Any]:
        """Convert ORM model to dictionary."""
        if not record:
            return None
        return {
            "timestamp": record.timestamp.isoformat() if record.timestamp else None,
            "snapshot": record.snapshot,
        }
