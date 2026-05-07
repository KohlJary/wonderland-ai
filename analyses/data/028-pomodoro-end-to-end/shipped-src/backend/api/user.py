"""User info endpoints: GET /user."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.backend.db import get_db
from src.backend.models import User

router = APIRouter()

# Hardcoded user_id = 1 for MVP
DEFAULT_USER_ID = 1


class UserResponse(BaseModel):
    id: int
    launch_date: str | None
    days_tracked: int


def _get_or_create_user(db: Session) -> User:
    """Ensure user exists."""
    user = db.query(User).filter(User.id == DEFAULT_USER_ID).first()
    if not user:
        user = User(id=DEFAULT_USER_ID)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.get("/user", response_model=UserResponse)
def get_user(db: Session = Depends(get_db)) -> UserResponse:
    """Get current user info including launch date and membership duration."""
    user = _get_or_create_user(db)

    # Compute days_tracked server-side
    days_tracked = 0
    if user.launch_date:
        now = datetime.now(timezone.utc)
        delta = now - user.launch_date
        days_tracked = delta.days

    return UserResponse(
        id=user.id,
        launch_date=user.launch_date.isoformat() if user.launch_date else None,
        days_tracked=days_tracked,
    )
