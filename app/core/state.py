import asyncio
from typing import Set

from fastapi import WebSocket

from app.services.alerts import AlertManager
from app.services.email_service import EmailService
from app.services.observer import SiteObserver
from app.services.price_history import PriceHistory
from app.services.replay_manager import ReplayManager
from app.services.sms_service import SMSService

alert_manager = AlertManager()
price_history = PriceHistory()
replay_manager = ReplayManager()

observer: SiteObserver | None = None
active_websockets: Set[WebSocket] = set()
background_task: asyncio.Task | None = None
shutdown_event = asyncio.Event()

email_service: EmailService | None = None
sms_service: SMSService | None = None
