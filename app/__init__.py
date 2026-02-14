"""
Commodities Observer Application
"""
# Import models to ensure they are registered with SQLAlchemy
from app.models.models import Alert, PriceHistory, Candle

__all__ = ["Alert", "PriceHistory", "Candle"]
