from fastapi import APIRouter

from app.api.v1.endpoints import alerts, replay, candles

api_router = APIRouter()

api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(replay.router, prefix="/replay", tags=["replay"])
api_router.include_router(candles.router, prefix="/candles", tags=["candles"])
