"""Session history and statistics endpoints: /sessions/history, /stats/*, /user."""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from src.backend.db import get_db
from src.backend.models import Session, User, Break

router = APIRouter()

# Hardcoded user_id = 1 for MVP
DEFAULT_USER_ID = 1


class HistorySessionResponse(BaseModel):
    """Session history entry schema."""
    id: int
    start_time: str
    completed_at: str
    duration_seconds: int
    break_duration_seconds: int
    break_skipped: bool


@router.get("/sessions/history", response_model=list[HistorySessionResponse])
def get_session_history(
    since_timestamp: int | None = Query(None),
    db: DBSession = Depends(get_db)
) -> list[HistorySessionResponse]:
    """Get completed sessions (most recent first)."""
    query = db.query(Session).filter(Session.state == "completed")
    
    # Apply since_timestamp filter if provided
    if since_timestamp is not None:
        since_dt = datetime.fromtimestamp(since_timestamp, tz=timezone.utc)
        query = query.filter(Session.completed_at >= since_dt)
    
    # Order by completed_at DESC (most recent first)
    sessions = query.order_by(Session.completed_at.desc()).all()
    
    result = []
    for session in sessions:
        # Find the break associated with this session
        break_obj = db.query(Break).filter(Break.session_id == session.id).first()
        
        # Compute break info
        break_duration_seconds = (break_obj.duration_minutes * 60) if break_obj else 0
        break_skipped = (break_obj.state == "skipped") if break_obj else False
        
        # Compute session duration
        start_dt = session.start_time if session.start_time else datetime.now(timezone.utc)
        completed_dt = session.completed_at if session.completed_at else start_dt
        duration_seconds = int((completed_dt - start_dt).total_seconds())
        
        result.append(HistorySessionResponse(
            id=session.id,
            start_time=start_dt.isoformat() if start_dt else None,
            completed_at=completed_dt.isoformat() if completed_dt else None,
            duration_seconds=duration_seconds,
            break_duration_seconds=break_duration_seconds,
            break_skipped=break_skipped,
        ))
    
    return result
