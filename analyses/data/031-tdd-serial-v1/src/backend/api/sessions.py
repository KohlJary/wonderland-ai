"""Session management API endpoints (Focus Session Timer, Feature 001).

Endpoints:
- POST /api/sessions/start          -> create a new session
- GET /api/sessions/<session_id>    -> get current session state
- POST /api/sessions/<session_id>/pause   -> pause a session
- POST /api/sessions/<session_id>/resume  -> resume a paused session
- POST /api/sessions/<session_id>/skip    -> skip a session (end early)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from src.backend.db import get_db
from src.backend.models import SessionStatus, CompletionType
from src.backend.models import Session as SessionModel

router = APIRouter()


# === Request/Response Pydantic models ===
class StartSessionRequest(BaseModel):
    """POST /api/sessions/start request body."""
    duration_seconds: int = Field(..., gt=0, description="Session duration in seconds, must be positive")

    @field_validator("duration_seconds")
    @classmethod
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError("duration_seconds must be positive")
        return v


class SessionResponse(BaseModel):
    """Session state response (shared across GET and mutations)."""
    session_id: str
    duration_seconds: int
    elapsed_ms: int
    status: str  # 'running', 'paused', 'completed'
    created_at: str
    completed_at: str | None = None
    completion_type: str | None = None


# === Endpoints ===
@router.post("/sessions/start", status_code=201)
def start_session(
    req: StartSessionRequest,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """
    POST /api/sessions/start
    Create a new focus/break session.
    
    Request: { "duration_seconds": 1500 }
    Response: { "session_id": "<UUID>", "elapsed_ms": 0, "status": "running", ... }
    """
    session = SessionModel(
        duration_seconds=req.duration_seconds,
        status=SessionStatus.RUNNING,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return SessionResponse(**session.to_dict())


@router.get("/sessions/{session_id}")
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """
    GET /api/sessions/<session_id>
    Fetch the current state of a session (including real-time elapsed_ms).
    """
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(**session.to_dict())


@router.post("/sessions/{session_id}/pause")
def pause_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """
    POST /api/sessions/<session_id>/pause
    Pause a running or paused session (idempotent).
    Freezes elapsed_ms at current value.
    """
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # If already completed, reject
    if session.status == SessionStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot pause a completed session")
    
    # If already paused, return current state (idempotent)
    if session.status == SessionStatus.PAUSED:
        return SessionResponse(**session.to_dict())
    
    # Transition from running to paused
    now = datetime.now(timezone.utc)
    session.pause_at = now
    session.frozen_elapsed_ms = session.elapsed_ms()
    session.status = SessionStatus.PAUSED
    db.commit()
    db.refresh(session)
    
    return SessionResponse(**session.to_dict())


@router.post("/sessions/{session_id}/resume")
def resume_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """
    POST /api/sessions/<session_id>/resume
    Resume a paused session, continuing from the freeze point (idempotent).
    """
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # If already completed, reject
    if session.status == SessionStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot resume a completed session")
    
    # If already running, return current state (idempotent)
    if session.status == SessionStatus.RUNNING:
        return SessionResponse(**session.to_dict())
    
    # Transition from paused to running
    # Adjust created_at so that the frozen elapsed becomes the new baseline
    # created_at_new = now - frozen_elapsed_ms
    now = datetime.now(timezone.utc)
    frozen_ms = session.frozen_elapsed_ms or 0
    from datetime import timedelta
    adjustment = timedelta(milliseconds=frozen_ms)
    session.created_at = now - adjustment
    
    session.pause_at = None
    session.frozen_elapsed_ms = None
    session.status = SessionStatus.RUNNING
    db.commit()
    db.refresh(session)
    
    return SessionResponse(**session.to_dict())


@router.post("/sessions/{session_id}/skip")
def skip_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """
    POST /api/sessions/<session_id>/skip
    Skip a session, ending it immediately (idempotent).
    Sets completion_type='skip'.
    """
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # If already completed, return current state (idempotent)
    if session.status == SessionStatus.COMPLETED:
        return SessionResponse(**session.to_dict())
    
    # Transition to completed
    now = datetime.now(timezone.utc)
    session.completed_at = now
    session.completion_type = CompletionType.SKIP
    session.status = SessionStatus.COMPLETED
    session.pause_at = None
    session.frozen_elapsed_ms = None
    db.commit()
    db.refresh(session)
    
    return SessionResponse(**session.to_dict())
