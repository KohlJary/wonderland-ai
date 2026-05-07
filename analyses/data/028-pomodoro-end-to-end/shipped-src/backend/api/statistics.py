"""Statistics endpoints: GET /stats/week, GET /stats/all-time."""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.backend.db import get_db
from src.backend.models import User, Session as SessionModel

router = APIRouter()

# Hardcoded user_id = 1 for MVP
DEFAULT_USER_ID = 1


class WeekStatsResponse(BaseModel):
    session_count: int
    total_duration_seconds: int
    week_start_date: str
    week_end_date: str


class AllTimeStatsResponse(BaseModel):
    session_count: int
    total_duration_seconds: int
    membership_duration_days: int


def _get_or_create_user(db: Session) -> User:
    """Ensure user exists."""
    user = db.query(User).filter(User.id == DEFAULT_USER_ID).first()
    if not user:
        user = User(id=DEFAULT_USER_ID)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _get_week_boundaries() -> tuple[datetime, datetime]:
    """Get Monday 00:00 UTC and Sunday 23:59:59 UTC for the current week."""
    now = datetime.now(timezone.utc)
    # weekday() returns 0=Monday, 6=Sunday
    days_since_monday = now.weekday()
    week_start = now - timedelta(days=days_since_monday)
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return week_start, week_end


@router.get("/stats/week", response_model=WeekStatsResponse)
def get_week_stats(db: Session = Depends(get_db)) -> WeekStatsResponse:
    """Get weekly statistics for the current week (Mon-Sun UTC)."""
    user = _get_or_create_user(db)
    week_start, week_end = _get_week_boundaries()

    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == user.id,
        SessionModel.state == "completed",
        SessionModel.completed_at >= week_start,
        SessionModel.completed_at <= week_end,
    ).all()

    session_count = len(sessions)
    total_duration_seconds = sum(s.duration_minutes * 60 for s in sessions)

    return WeekStatsResponse(
        session_count=session_count,
        total_duration_seconds=total_duration_seconds,
        week_start_date=week_start.isoformat(),
        week_end_date=week_end.isoformat(),
    )


@router.get("/stats/all-time", response_model=AllTimeStatsResponse)
def get_all_time_stats(db: Session = Depends(get_db)) -> AllTimeStatsResponse:
    """Get all-time statistics and membership duration."""
    user = _get_or_create_user(db)

    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == user.id,
        SessionModel.state == "completed",
    ).all()

    session_count = len(sessions)
    total_duration_seconds = sum(s.duration_minutes * 60 for s in sessions)

    # Compute membership_duration_days (server-side)
    membership_duration_days = 0
    if user.launch_date:
        now = datetime.now(timezone.utc)
        delta = now - user.launch_date
        membership_duration_days = delta.days

    return AllTimeStatsResponse(
        session_count=session_count,
        total_duration_seconds=total_duration_seconds,
        membership_duration_days=membership_duration_days,
    )
