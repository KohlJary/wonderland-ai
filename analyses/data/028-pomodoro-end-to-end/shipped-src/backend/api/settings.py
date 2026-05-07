"""Settings management endpoints: GET /settings, PATCH /settings."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.db import get_db
from src.backend.models import User, UserSettings

router = APIRouter()

# Hardcoded user_id = 1 for MVP
DEFAULT_USER_ID = 1


class SettingsResponse(BaseModel):
    session_duration_minutes: int
    break_duration_minutes: int


class SettingsPatch(BaseModel):
    session_duration_minutes: int | None = Field(None, ge=1, le=180)
    break_duration_minutes: int | None = Field(None, ge=1, le=180)


def _get_or_create_user(db: Session) -> User:
    """Ensure user exists."""
    user = db.query(User).filter(User.id == DEFAULT_USER_ID).first()
    if not user:
        user = User(id=DEFAULT_USER_ID)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _get_or_create_settings(db: Session, user_id: int) -> UserSettings:
    """Ensure user settings exist."""
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        settings = UserSettings(
            user_id=user_id,
            session_duration_minutes=25,
            break_duration_minutes=5,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("/settings", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)) -> SettingsResponse:
    """Get current user settings."""
    user = _get_or_create_user(db)
    settings = _get_or_create_settings(db, user.id)
    return SettingsResponse(**settings.to_dict())


@router.patch("/settings", response_model=SettingsResponse)
def patch_settings(
    payload: SettingsPatch,
    db: Session = Depends(get_db)
) -> SettingsResponse:
    """Update user settings (partial update allowed)."""
    user = _get_or_create_user(db)
    settings = _get_or_create_settings(db, user.id)

    # Apply updates only for provided fields
    if payload.session_duration_minutes is not None:
        settings.session_duration_minutes = payload.session_duration_minutes
    if payload.break_duration_minutes is not None:
        settings.break_duration_minutes = payload.break_duration_minutes

    db.commit()
    db.refresh(settings)
    return SettingsResponse(**settings.to_dict())
