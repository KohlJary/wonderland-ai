"""Break management endpoints: /break/current, /break/skip."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.backend.db import get_db
from src.backend.models import User, Break as BreakModel

router = APIRouter()

# Hardcoded user_id = 1 for MVP
DEFAULT_USER_ID = 1


class BreakResponse(BaseModel):
    id: int
    state: str
    duration_minutes: int
    start_time: str
    completed_at: str | None
    remaining_seconds: int
    skip_available: bool


def _get_or_create_user(db: Session) -> User:
    """Ensure user exists."""
    user = db.query(User).filter(User.id == DEFAULT_USER_ID).first()
    if not user:
        user = User(id=DEFAULT_USER_ID)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _get_active_break(db: Session, user_id: int) -> BreakModel | None:
    """Get the currently active break for a user, if any."""
    return db.query(BreakModel).filter(
        BreakModel.user_id == user_id,
        BreakModel.state == "active",
    ).first()


@router.get("/break/current", response_model=BreakResponse)
def get_current_break(db: Session = Depends(get_db)) -> BreakResponse:
    """Get the currently active break."""
    user = _get_or_create_user(db)
    active = _get_active_break(db, user.id)

    if not active:
        raise HTTPException(status_code=404, detail="No active break")

    return BreakResponse(**active.to_dict())


@router.post("/break/skip", response_model=BreakResponse)
def skip_break(db: Session = Depends(get_db)) -> BreakResponse:
    """Skip the current break. Idempotent — returns the skipped break."""
    user = _get_or_create_user(db)
    active = _get_active_break(db, user.id)

    if not active:
        raise HTTPException(status_code=404, detail="No active break")

    # If already skipped or completed, return it
    if active.state != "active":
        return BreakResponse(**active.to_dict())

    # Skip the break
    now = datetime.now(timezone.utc)
    active.state = "skipped"
    active.completed_at = now
    db.commit()
    db.refresh(active)

    return BreakResponse(**active.to_dict())
