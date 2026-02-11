from typing import List

from pydantic import BaseModel


class CreateAlertRequest(BaseModel):
    pair: str
    target_price: float
    condition: str  # "above", "below", or "equal"
    channels: List[str] = ["email"]  # ["email"], ["sms"], or ["email", "sms"]
    email: str = ""
    phone: str = ""
    custom_message: str = ""  # Optional custom message for the alert
