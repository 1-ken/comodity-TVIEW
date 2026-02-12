"""
SQLAlchemy ORM models for commodities application.
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.database import Base


class Alert(Base):
    """ORM model for price alerts."""
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair = Column(String(50), nullable=False, index=True)
    target_price = Column(Float, nullable=False)
    condition = Column(String(20), nullable=False)  # "above", "below", "equal"
    status = Column(String(20), default="active")  # "active", "triggered", "disabled"
    email = Column(String(255), default="")
    phone = Column(String(20), default="")
    channels = Column(JSON, default=list)  # ["email"], ["sms"], or ["email", "sms"]
    custom_message = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    triggered_at = Column(DateTime, nullable=True)
    last_checked_price = Column(Float, nullable=True)

    __table_args__ = (
        Index('idx_alert_pair_status', 'pair', 'status'),
    )


class PriceHistory(Base):
    """ORM model for historical price snapshots."""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    snapshot = Column(JSON, nullable=False)  # Full snapshot data

    __table_args__ = (
        Index('idx_price_history_timestamp', 'timestamp'),
    )


class Candle(Base):
    """ORM model for OHLC candles across multiple timeframes."""
    __tablename__ = "candles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pair = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)  # "1m", "5m", "15m", etc.
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0)
    
    __table_args__ = (
        Index('idx_candle_pair_timeframe_ts', 'pair', 'timeframe', 'timestamp'),
    )
