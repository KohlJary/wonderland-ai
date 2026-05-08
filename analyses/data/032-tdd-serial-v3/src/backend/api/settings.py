"""Settings endpoints.

GET /settings — read user settings (with defaults)
POST /settings — write user settings
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from src.backend.db import get_db
from src.backend.models import UserSettings

router = APIRouter()


class SettingsRequest(BaseModel):
    """Request to update user settings."""
    focus_duration_seconds: int = Field(default=None, ge=60, le=7200, description="Focus duration in seconds")
    break_duration_seconds: int = Field(default=None, ge=60, le=1800, description="Break duration in seconds")
    sound_enabled: bool = Field(default=None, description="Enable sound notifications")


class SettingsResponse(BaseModel):
    """User settings response."""
    focus_duration_seconds: int
    break_duration_seconds: int
    sound_enabled: bool


@router.get("/settings", response_model=SettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
) -> SettingsResponse:
    """Retrieve user settings.
    
    Returns settings for the current user (hardcoded to "default" for v1).
    If no settings exist, returns defaults:
    - focus_duration_seconds: 1500 (25 minutes)
    - break_duration_seconds: 300 (5 minutes)
    - sound_enabled: true
    """
    user_id = "default"
    
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    
    if not settings:
        # Return defaults
        return SettingsResponse(
            focus_duration_seconds=1500,
            break_duration_seconds=300,
            sound_enabled=True,
        )
    
    return SettingsResponse(**settings.to_dict())


@router.post("/settings", response_model=SettingsResponse, status_code=200)
def update_settings(
    payload: SettingsRequest,
    db: Session = Depends(get_db),
) -> SettingsResponse:
    """Update user settings.
    
    Updates any of the provided fields. Validates:
    - focus_duration_seconds: [60, 7200]
    - break_duration_seconds: [60, 1800]
    - sound_enabled: boolean
    
    Returns 200 with updated settings or 400 if validation fails.
    """
    user_id = "default"
    
    # Get or create settings
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
    
    # Update fields if provided
    if payload.focus_duration_seconds is not None:
        if payload.focus_duration_seconds < 60 or payload.focus_duration_seconds > 7200:
            raise HTTPException(status_code=400, detail="focus_duration_seconds must be between 60 and 7200")
        settings.focus_duration_seconds = payload.focus_duration_seconds
    
    if payload.break_duration_seconds is not None:
        if payload.break_duration_seconds < 60 or payload.break_duration_seconds > 1800:
            raise HTTPException(status_code=400, detail="break_duration_seconds must be between 60 and 1800")
        settings.break_duration_seconds = payload.break_duration_seconds
    
    if payload.sound_enabled is not None:
        settings.sound_enabled = payload.sound_enabled
    
    try:
        db.commit()
        db.refresh(settings)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update settings")
    
    return SettingsResponse(**settings.to_dict())
