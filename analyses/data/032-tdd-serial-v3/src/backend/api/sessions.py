"""Session logging and history endpoints.

POST /sessions/log — logs completed session (focus or break)
GET /sessions — retrieves sessions for a given date
POST /sessions/break — creates a break session
PATCH /sessions/{session_id} — adjusts session or performs actions
DELETE /sessions/{session_id} — skips/cancels a session
"""

from datetime import datetime, timezone, date as date_type
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.backend.db import get_db
from src.backend.models import SessionLog, SessionType, Session as SessionModel, SessionStatus

router = APIRouter()


class SessionLogRequest(BaseModel):
    """Request to log a completed session.
    
    Invariants enforced:
    - type must be 'focus' or 'break'
    - duration_actual must be <= duration_configured + 5% (timer drift tolerance)
    - completed_at must be ISO8601 and not in the future
    """
    type: str = Field(..., description="'focus' or 'break'")
    duration_configured_seconds: int = Field(..., ge=0, description="Configured session duration in seconds")
    duration_actual_seconds: int = Field(..., ge=0, description="Actual elapsed time in seconds")
    completed_at: str = Field(..., description="ISO8601 timestamp of session completion")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("focus", "break"):
            raise ValueError("type must be 'focus' or 'break'")
        return v

    @field_validator("duration_actual_seconds")
    @classmethod
    def validate_duration_actual(cls, v: int, info) -> int:
        # This validator runs after type, so we can check duration drift
        if "duration_configured_seconds" in info.data:
            configured = info.data["duration_configured_seconds"]
            # Allow up to 5% timer drift
            max_drift = configured * 0.05
            if v > configured + max_drift:
                raise ValueError(
                    f"duration_actual ({v}s) exceeds configured ({configured}s) + 5% drift tolerance"
                )
        return v

    @field_validator("completed_at")
    @classmethod
    def validate_completed_at(cls, v: str) -> str:
        # Validate ISO8601 format
        try:
            dt = datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("completed_at must be ISO8601 format (e.g., '2024-01-15T14:30:00+00:00')")
        
        # Ensure it's not in the future (allow 5s clock skew tolerance)
        now = datetime.now(timezone.utc)
        if dt > now and (dt - now).total_seconds() > 5:
            raise ValueError("completed_at cannot be in the future")
        
        return v


class SessionLogResponse(BaseModel):
    """Response after logging a session."""
    session_id: str
    acknowledged: bool = True


class CreateBreakSessionRequest(BaseModel):
    """Request to create a break session.
    
    Defaults to configured break duration from settings.
    """
    duration_seconds: int = Field(default=None, ge=60, le=1800, description="Break duration in seconds")


class SessionResponse(BaseModel):
    """Response for session operations."""
    id: str
    type: str
    status: str
    duration_seconds: int
    created_at: str
    updated_at: str


class UpdateSessionRequest(BaseModel):
    """Request to update a session."""
    duration_seconds: int = Field(default=None, ge=60, le=1800, description="New duration in seconds")
    action: str = Field(default=None, description="Action: 'pause', 'resume', 'skip'")


class SessionTotals(BaseModel):
    """Aggregated statistics for sessions on a given date."""
    focus_count: int = 0
    break_count: int = 0
    focus_minutes: int = 0
    break_minutes: int = 0


class SessionListResponse(BaseModel):
    """Response for listing sessions for a date."""
    sessions: list[dict]
    totals: SessionTotals


@router.post("/sessions/log", response_model=SessionLogResponse, status_code=200)
def log_session(
    payload: SessionLogRequest,
    db: Session = Depends(get_db),
) -> SessionLogResponse:
    """Log a completed session.
    
    Persists the session to the database. Handles idempotency by using a
    unique constraint on (user_id, type, completed_at). If the exact same
    session is submitted twice, returns the existing session_id.
    
    Also auto-creates a break session if a focus session completes, and
    marks the focus session as COMPLETED in the Session (in-progress) table.
    
    Validates:
    - type is 'focus' or 'break'
    - duration_actual <= duration_configured + 5%
    - completed_at is ISO8601 and not in the future
    
    Returns 200 with session_id on success, 4xx on validation error,
    5xx on persistence failure.
    """
    # Hardcode user_id to "default" for v1 (no auth yet)
    user_id = "default"
    
    # Generate session_id (deterministic from user_id + completed_at + type would be better for true idempotency,
    # but UUID is simpler and still handles retries correctly)
    session_id = str(uuid4())
    
    # Parse completed_at timestamp
    try:
        completed_at = datetime.fromisoformat(payload.completed_at)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid completed_at timestamp")
    
    # Ensure timezone-aware
    if completed_at.tzinfo is None:
        completed_at = completed_at.replace(tzinfo=timezone.utc)
    
    # Convert string type to SessionType enum
    try:
        session_type = SessionType(payload.type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid session type: {payload.type}")
    
    # Create and persist the session log
    session_log = SessionLog(
        id=session_id,
        user_id=user_id,
        type=session_type,
        duration_configured_seconds=payload.duration_configured_seconds,
        duration_actual_seconds=payload.duration_actual_seconds,
        completed_at=completed_at,
    )
    
    try:
        db.add(session_log)
        db.commit()
        db.refresh(session_log)
    except IntegrityError as e:
        # Unique constraint violation — idempotent retry
        # Query for the existing session and return its ID
        db.rollback()
        existing = db.query(SessionLog).filter(
            SessionLog.user_id == user_id,
            SessionLog.type == session_type,
            SessionLog.completed_at == completed_at,
        ).first()
        
        if existing:
            return SessionLogResponse(session_id=existing.id)
        
        # Some other integrity error
        raise HTTPException(status_code=409, detail="Session already exists")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to persist session")
    
    # Update the corresponding in-progress Session record to COMPLETED
    # This ensures the Session table reflects the completion
    if session_type == SessionType.FOCUS:
        in_progress_session = db.query(SessionModel).filter(
            SessionModel.user_id == user_id,
            SessionModel.type == SessionType.FOCUS,
            SessionModel.status == SessionStatus.RUNNING,
        ).order_by(SessionModel.created_at.desc()).first()
        
        if in_progress_session:
            in_progress_session.status = SessionStatus.COMPLETED
            try:
                db.commit()
            except Exception:
                db.rollback()
                # Completion update failure shouldn't fail the log response
                pass
    elif session_type == SessionType.BREAK:
        in_progress_session = db.query(SessionModel).filter(
            SessionModel.user_id == user_id,
            SessionModel.type == SessionType.BREAK,
            SessionModel.status == SessionStatus.RUNNING,
        ).order_by(SessionModel.created_at.desc()).first()
        
        if in_progress_session:
            in_progress_session.status = SessionStatus.COMPLETED
            try:
                db.commit()
            except Exception:
                db.rollback()
                # Completion update failure shouldn't fail the log response
                pass
    
    # Auto-create a break session if a focus session just completed
    if session_type == SessionType.FOCUS:
        # Use default break duration (5 min = 300 seconds) for now
        # In a future update, this would read from user settings
        default_break_duration = 300
        
        break_session = SessionModel(
            id=str(uuid4()),
            user_id=user_id,
            type=SessionType.BREAK,
            status=SessionStatus.RUNNING,
            duration_seconds=default_break_duration,
        )
        
        try:
            db.add(break_session)
            db.commit()
        except Exception as e:
            db.rollback()
            # Break creation failure doesn't fail the focus log, but log it
            # In production, this would be a monitored event
            pass
    
    return SessionLogResponse(session_id=session_log.id)


@router.get("/sessions", response_model=SessionListResponse)
def list_sessions(
    date: str = Query(..., description="ISO8601 date (e.g., '2024-01-15')"),
    db: Session = Depends(get_db),
) -> SessionListResponse:
    """Retrieve all sessions for a given date.
    
    Query parameter:
    - date: ISO8601 date string (e.g., '2024-01-15')
    
    Returns sessions for that date (in UTC timezone) and aggregated totals.
    """
    user_id = "default"
    
    # Parse the date
    try:
        target_date = date_type.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format; use ISO8601 (e.g., '2024-01-15')")
    
    # Query sessions for this user on this date
    # Convert date to UTC midnight boundaries
    day_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    day_end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    sessions = db.query(SessionLog).filter(
        SessionLog.user_id == user_id,
        SessionLog.completed_at >= day_start,
        SessionLog.completed_at <= day_end,
    ).order_by(SessionLog.completed_at).all()
    
    # Convert to dicts
    session_dicts = [s.to_dict() for s in sessions]
    
    # Calculate totals
    focus_count = sum(1 for s in sessions if s.type == SessionType.FOCUS)
    break_count = sum(1 for s in sessions if s.type == SessionType.BREAK)
    focus_seconds = sum(
        s.duration_actual_seconds for s in sessions if s.type == SessionType.FOCUS
    )
    break_seconds = sum(
        s.duration_actual_seconds for s in sessions if s.type == SessionType.BREAK
    )
    
    totals = SessionTotals(
        focus_count=focus_count,
        break_count=break_count,
        focus_minutes=focus_seconds // 60,
        break_minutes=break_seconds // 60,
    )
    
    return SessionListResponse(sessions=session_dicts, totals=totals)


@router.post("/sessions/break", response_model=SessionResponse, status_code=201)
def create_break_session(
    payload: CreateBreakSessionRequest = None,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Create a new break session.
    
    Creates an in-progress break session with the specified duration.
    If no duration is provided, uses the configured default (300 seconds / 5 minutes).
    
    Returns 201 with session details on success.
    """
    user_id = "default"
    
    # Use provided duration or default to 300 seconds (5 minutes)
    duration = payload.duration_seconds if payload and payload.duration_seconds else 300
    
    # Validate duration is in range
    if duration < 60 or duration > 1800:
        raise HTTPException(status_code=400, detail="duration_seconds must be between 60 and 1800")
    
    # Create the break session
    session_id = str(uuid4())
    break_session = SessionModel(
        id=session_id,
        user_id=user_id,
        type=SessionType.BREAK,
        status=SessionStatus.RUNNING,
        duration_seconds=duration,
    )
    
    try:
        db.add(break_session)
        db.commit()
        db.refresh(break_session)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create break session")
    
    return SessionResponse(**break_session.to_dict())


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Retrieve a session by ID.
    
    Returns the session details or 404 if not found.
    """
    user_id = "default"
    
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == user_id,
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(**session.to_dict())


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: str,
    payload: UpdateSessionRequest,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Update a session (adjust duration or perform actions).
    
    Actions:
    - duration_seconds: update the session's configured duration
    - action=pause: pause the session
    - action=resume: resume the session
    - action=skip: mark the session as skipped
    
    Returns 200 with updated session or 404 if not found.
    """
    user_id = "default"
    
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == user_id,
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Handle duration update
    if payload.duration_seconds is not None:
        if payload.duration_seconds < 60 or payload.duration_seconds > 1800:
            raise HTTPException(status_code=400, detail="duration_seconds must be between 60 and 1800")
        session.duration_seconds = payload.duration_seconds
    
    # Handle action
    if payload.action:
        if payload.action == "pause":
            if session.status != SessionStatus.RUNNING:
                raise HTTPException(status_code=400, detail="Can only pause a running session")
            session.status = SessionStatus.PAUSED
        elif payload.action == "resume":
            if session.status != SessionStatus.PAUSED:
                raise HTTPException(status_code=400, detail="Can only resume a paused session")
            session.status = SessionStatus.RUNNING
        elif payload.action == "skip":
            # Can skip running or paused sessions
            if session.status in (SessionStatus.COMPLETED, SessionStatus.SKIPPED):
                # Already complete/skipped; this is idempotent
                return SessionResponse(**session.to_dict())
            session.status = SessionStatus.SKIPPED
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {payload.action}")
    
    try:
        db.commit()
        db.refresh(session)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update session")
    
    return SessionResponse(**session.to_dict())


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Delete (skip) a session.
    
    Marks the session as skipped. Returns 204 (No Content) on success
    or 404 if not found.
    """
    user_id = "default"
    
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == user_id,
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Mark as skipped instead of deleting
    session.status = SessionStatus.SKIPPED
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to skip session")
    
    # Return 204 No Content (don't return the response body)
    return None
