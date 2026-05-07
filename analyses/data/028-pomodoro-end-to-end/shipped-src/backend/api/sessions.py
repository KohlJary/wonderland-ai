"""Session lifecycle endpoints: /session/start, /session/{id}/stop, /session/current."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.backend.db import get_db
from src.backend.models import User, UserSettings, Session as SessionModel, Break as BreakModel

router = APIRouter()

# Hardcoded user_id = 1 for MVP
DEFAULT_USER_ID = 1


class SessionResponse(BaseModel):
    id: int
    state: str
    duration_minutes: int
    start_time: str
    completed_at: str | None
    remaining_seconds: int


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


def _get_active_session(db: Session, user_id: int) -> SessionModel | None:
    """Get the currently active session for a user, if any."""
    return db.query(SessionModel).filter(
        SessionModel.user_id == user_id,
        SessionModel.state == "active",
    ).first()


def _get_active_break(db: Session, user_id: int) -> BreakModel | None:
    """Get the currently active break for a user, if any."""
    return db.query(BreakModel).filter(
        BreakModel.user_id == user_id,
        BreakModel.state == "active",
    ).first()


@router.post("/session/start", response_model=SessionResponse)
def start_session(db: Session = Depends(get_db)) -> SessionResponse:
    """Start a new session or return the existing active one (idempotent)."""
    user = _get_or_create_user(db)
    settings = _get_or_create_settings(db, user.id)

    # Check if a session is already active
    active = _get_active_session(db, user.id)
    if active:
        return SessionResponse(**active.to_dict())

    # Create new session with duration from settings
    now = datetime.now(timezone.utc)
    session = SessionModel(
        user_id=user.id,
        state="active",
        duration_minutes=settings.session_duration_minutes,
        start_time=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Set launch_date on first session
    if user.launch_date is None:
        user.launch_date = now
        db.commit()

    return SessionResponse(**session.to_dict())


@router.get("/session/current", response_model=SessionResponse)
def get_current_session(db: Session = Depends(get_db)) -> SessionResponse:
    """Get the currently active session."""
    user = _get_or_create_user(db)
    active = _get_active_session(db, user.id)

    if not active:
        raise HTTPException(status_code=404, detail="No active session")

    return SessionResponse(**active.to_dict())


@router.post("/session/{session_id}/stop", response_model=SessionResponse)
def stop_session(session_id: int, db: Session = Depends(get_db)) -> SessionResponse:
    """Stop (complete) a session. Idempotent — returns the completed session."""
    user = _get_or_create_user(db)
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # If already completed, return it
    if session.state == "completed":
        return SessionResponse(**session.to_dict())

    # Complete the session
    now = datetime.now(timezone.utc)
    session.state = "completed"
    session.completed_at = now
    db.commit()
    db.refresh(session)

    # Auto-create a break if one doesn't already exist
    existing_break = db.query(BreakModel).filter(
        BreakModel.session_id == session_id,
    ).first()

    if not existing_break:
        settings = _get_or_create_settings(db, user.id)
        break_obj = BreakModel(
            user_id=user.id,
            session_id=session_id,
            state="active",
            duration_minutes=settings.break_duration_minutes,
            start_time=now,
        )
        db.add(break_obj)
        db.commit()

    return SessionResponse(**session.to_dict())
