"""
Alert management system for price notifications - PostgreSQL version.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.models import Alert as AlertModel

logger = logging.getLogger(__name__)

# Asset-specific tolerances for zero-tolerance market tracking
ASSET_TOLERANCES = {
    # Forex Pairs - very tight tolerance
    "EURUSD": 0.0002,
    "GBPUSD": 0.0002,

    # Commodities - exact match (±0.0)
    "GOLD": 0.0,
    "SILVER": 0.0,
    "USOIL": 0.2,

    # Crypto - varies by asset
    "BTCUSD": 50.0,
    "BTCUSDT": 50.0,
    "ETHUSD": 0.0,
    "ETHUSDT": 0.0,

    # Indices - exact match (±0.0)
    "SPX": 0.0,
    "DJI": 0.0,
    "NDQ": 0.0,

    # Stocks - varies by asset
    "AAPL": 0.5,
    "TSLA": 1.0,
    "NFLX": 0.1,

    # Forex Indices
    "DXY": 0.1,
    "USDJPY": 0.5,

    # Volatility
    "VIX": 0.1,
}


class AlertManager:
    """Manages price alerts and persistence in PostgreSQL using session-per-operation pattern."""

    def __init__(self):
        """Initialize alert manager. No persistent session stored."""
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

    def create_alert(
        self,
        pair: str,
        target_price: float,
        condition: str,
        email: str = "",
        channels: List[str] = None,
        phone: str = "",
        custom_message: str = "",
    ) -> Dict[str, Any]:
        """Create a new alert."""
        if channels is None:
            channels = ["email"]

        with self._get_session() as db:
            alert = AlertModel(
                id=uuid.uuid4(),
                pair=pair,
                target_price=target_price,
                condition=condition,
                email=email,
                channels=channels,
                phone=phone,
                custom_message=custom_message,
                status="active",
                created_at=datetime.utcnow(),
            )
            db.add(alert)
            db.flush()  # Get the ID without committing yet
            db.refresh(alert)
            result = self._to_dict(alert)
            logger.info("Created alert %s for %s at %s via %s", alert.id, pair, target_price, channels)
            return result

    def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get alert by ID."""
        with self._get_session() as db:
            try:
                # Ensure alert_id is a valid UUID string
                alert_uuid = uuid.UUID(str(alert_id)) if not isinstance(alert_id, uuid.UUID) else alert_id
                alert = db.query(AlertModel).filter(AlertModel.id == alert_uuid).first()
                return self._to_dict(alert) if alert else None
            except (ValueError, AttributeError) as e:
                logger.error("Invalid alert_id format: %s - %s", alert_id, e)
                return None

    def get_all_alerts(self) -> List[Dict[str, Any]]:
        """Get all alerts."""
        with self._get_session() as db:
            alerts = db.query(AlertModel).all()
            return [self._to_dict(a) for a in alerts]

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get only active alerts."""
        with self._get_session() as db:
            alerts = db.query(AlertModel).filter(AlertModel.status == "active").all()
            return [self._to_dict(a) for a in alerts]

    def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert."""
        with self._get_session() as db:
            try:
                alert_uuid = uuid.UUID(str(alert_id)) if not isinstance(alert_id, uuid.UUID) else alert_id
                alert = db.query(AlertModel).filter(AlertModel.id == alert_uuid).first()
                if alert:
                    db.delete(alert)
                    logger.info("Deleted alert %s", alert_id)
                    return True
                return False
            except (ValueError, AttributeError) as e:
                logger.error("Invalid alert_id format: %s - %s", alert_id, e)
                return False

    def trigger_alert(self, alert_id: str, current_price: float) -> bool:
        """Mark an alert as triggered."""
        with self._get_session() as db:
            try:
                # Ensure alert_id is a valid UUID
                alert_uuid = uuid.UUID(str(alert_id)) if not isinstance(alert_id, uuid.UUID) else alert_id
                alert = db.query(AlertModel).filter(AlertModel.id == alert_uuid).first()
                if alert:
                    alert.status = "triggered"
                    alert.triggered_at = datetime.utcnow()
                    alert.last_checked_price = current_price
                    logger.info("Triggered alert %s at price %s", alert_id, current_price)
                    return True
                return False
            except (ValueError, AttributeError) as e:
                logger.error("Invalid alert_id format: %s - %s", alert_id, e)
                return False

    @staticmethod
    def _get_tolerance(pair: str) -> float:
        """
        Get asset-specific tolerance for price comparison.
        Uses predefined tolerances for each asset type for zero-tolerance market tracking.
        Default tolerance if asset not in map: 0.01
        """
        return ASSET_TOLERANCES.get(pair, 0.01)

    def check_alerts(self, pairs_data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Check if any active alerts should be triggered.
        Returns list of triggered alerts with their data.
        """
        triggered = []

        # Create price lookup - remove commas from price strings first
        prices = {item["pair"]: float(item["price"].replace(",", "")) for item in pairs_data}

        active_alerts = self.get_active_alerts()

        for alert_dict in active_alerts:
            if alert_dict["pair"] not in prices:
                continue

            current_price = prices[alert_dict["pair"]]

            should_trigger = False
            if alert_dict["condition"] == "above" and current_price >= alert_dict["target_price"]:
                should_trigger = True
            elif alert_dict["condition"] == "below" and current_price <= alert_dict["target_price"]:
                should_trigger = True
            elif alert_dict["condition"] == "equal":
                tolerance = self._get_tolerance(alert_dict["pair"])
                if abs(current_price - alert_dict["target_price"]) <= tolerance:
                    should_trigger = True
                    logger.info(
                        "Equal alert triggered: %s price=%s target=%s tolerance=±%s",
                        alert_dict["pair"],
                        f"{current_price:.6f}",
                        f"{alert_dict['target_price']:.6f}",
                        f"{tolerance:.6f}",
                    )

            if should_trigger:
                self.trigger_alert(alert_dict["id"], current_price)
                triggered.append({
                    "alert": alert_dict,
                    "current_price": current_price,
                })

        return triggered

    @staticmethod
    def _to_dict(alert: AlertModel) -> Dict[str, Any]:
        """Convert alert ORM model to dictionary."""
        if not alert:
            return None
        return {
            "id": str(alert.id),
            "pair": alert.pair,
            "target_price": alert.target_price,
            "condition": alert.condition,
            "status": alert.status,
            "email": alert.email,
            "phone": alert.phone,
            "channels": alert.channels or [],
            "custom_message": alert.custom_message,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
            "last_checked_price": alert.last_checked_price,
        }
