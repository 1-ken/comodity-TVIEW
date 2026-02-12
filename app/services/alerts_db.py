"""
Alert management system for price notifications - PostgreSQL version.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

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
    """Manages price alerts and persistence in PostgreSQL."""

    def __init__(self):
        """Initialize with database session."""
        self.db: Session = SessionLocal()

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
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        logger.info("Created alert %s for %s at %s via %s", alert.id, pair, target_price, channels)
        return self._to_dict(alert)

    def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get alert by ID."""
        alert = self.db.query(AlertModel).filter(AlertModel.id == alert_id).first()
        return self._to_dict(alert) if alert else None

    def get_all_alerts(self) -> List[Dict[str, Any]]:
        """Get all alerts."""
        alerts = self.db.query(AlertModel).all()
        return [self._to_dict(a) for a in alerts]

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get only active alerts."""
        alerts = self.db.query(AlertModel).filter(AlertModel.status == "active").all()
        return [self._to_dict(a) for a in alerts]

    def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert."""
        alert = self.db.query(AlertModel).filter(AlertModel.id == alert_id).first()
        if alert:
            self.db.delete(alert)
            self.db.commit()
            logger.info("Deleted alert %s", alert_id)
            return True
        return False

    def trigger_alert(self, alert_id: str, current_price: float) -> bool:
        """Mark an alert as triggered."""
        alert = self.db.query(AlertModel).filter(AlertModel.id == alert_id).first()
        if alert:
            alert.status = "triggered"
            alert.triggered_at = datetime.utcnow()
            alert.last_checked_price = current_price
            self.db.commit()
            logger.info("Triggered alert %s at price %s", alert_id, current_price)
            return True
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

    def close(self) -> None:
        """Close database session."""
        self.db.close()
