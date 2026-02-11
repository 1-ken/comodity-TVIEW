from fastapi import APIRouter, HTTPException

from app.core import state
from app.schemas.alerts import CreateAlertRequest

router = APIRouter()


@router.post("")
async def create_alert(request: CreateAlertRequest):
    """Create a new price alert."""
    if request.condition not in ["above", "below", "equal"]:
        raise HTTPException(status_code=400, detail="Condition must be 'above', 'below', or 'equal'")

    if not request.channels:
        raise HTTPException(status_code=400, detail="At least one channel (email or sms) must be selected")

    invalid_channels = set(request.channels) - {"email", "sms"}
    if invalid_channels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid channels: {invalid_channels}. Must be 'email' or 'sms'",
        )

    if "email" in request.channels and not request.email:
        raise HTTPException(status_code=400, detail="Email is required for email alerts")
    if "sms" in request.channels and not request.phone:
        raise HTTPException(status_code=400, detail="Phone is required for SMS alerts")

    alert = state.alert_manager.create_alert(
        pair=request.pair,
        target_price=request.target_price,
        condition=request.condition,
        email=request.email,
        channels=request.channels,
        phone=request.phone,
        custom_message=request.custom_message,
    )
    return {"success": True, "alert": alert.to_dict()}


@router.get("")
async def get_alerts():
    """Get all alerts."""
    all_alerts = state.alert_manager.get_all_alerts()
    return {
        "total": len(all_alerts),
        "active": [a.to_dict() for a in all_alerts if a.status == "active"],
        "triggered": [a.to_dict() for a in all_alerts if a.status == "triggered"],
        "all": [a.to_dict() for a in all_alerts],
    }


@router.get("/{alert_id}")
async def get_alert(alert_id: str):
    """Get specific alert."""
    alert = state.alert_manager.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert.to_dict()


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert."""
    if state.alert_manager.delete_alert(alert_id):
        return {"success": True, "message": "Alert deleted"}
    raise HTTPException(status_code=404, detail="Alert not found")
