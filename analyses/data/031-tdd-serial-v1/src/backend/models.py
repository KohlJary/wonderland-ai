"""SQLAlchemy models for the Focus Session Timer and related features."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import uuid

from sqlalchemy import Column, DateTime, Integer, String, func, Enum as SQLEnum
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SessionStatus(str, Enum):
    """Session state machine: running -> paused -> completed, or running -> completed directly."""
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class CompletionType(str, Enum):
    """How a session ended: timeout (timer expired naturally) or skip (user skipped)."""
    TIMEOUT = "timeout"
    SKIP = "skip"


class Session(Base):
    """
    A focus or break session with real-time elapsed tracking.
    
    Invariants:
    - session_id is a UUID v4, unique, immutable
    - duration_seconds > 0
    - created_at is set once and never changes
    - status transitions follow: running -> paused -> running (cycle) -> completed
    - elapsed_ms is computed as (now - created_at) when running,
      or (pause_at - created_at) when paused
    - pause_at and frozen_elapsed_ms are set only when transitioning to paused
    - completed_at is set only on completion
    - completion_type is set only on completion
    """

    __tablename__ = "sessions"

    # Core identity and configuration
    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    duration_seconds = Column(Integer, nullable=False)
    status = Column(SQLEnum(SessionStatus), nullable=False, default=SessionStatus.RUNNING)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    pause_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Pause state
    frozen_elapsed_ms = Column(Integer, nullable=True)
    
    # Completion metadata
    completion_type = Column(SQLEnum(CompletionType), nullable=True)

    def elapsed_ms(self) -> int:
        """
        Compute elapsed time in milliseconds.
        
        If running: elapsed = now - created_at
        If paused: elapsed = pause_at - created_at (stored in frozen_elapsed_ms)
        If completed: elapsed = completed_at - created_at
        """
        now = datetime.now(timezone.utc)
        
        if self.status == SessionStatus.PAUSED:
            # Use frozen time
            return self.frozen_elapsed_ms or 0
        elif self.status == SessionStatus.COMPLETED:
            # Use completion time
            if self.completed_at:
                delta = self.completed_at - self.created_at
                return int(delta.total_seconds() * 1000)
            return 0
        else:  # RUNNING
            # Compute from wall clock
            delta = now - self.created_at
            return int(delta.total_seconds() * 1000)

    def to_dict(self) -> dict:
        """Convert session to API response dict."""
        return {
            "session_id": self.session_id,
            "duration_seconds": self.duration_seconds,
            "elapsed_ms": self.elapsed_ms(),
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "completion_type": self.completion_type.value if self.completion_type else None,
        }


class SessionEvent(Base):
    """
    Event logged when a session completes (focus or break).
    Used by feature 003 for daily review queries.
    
    Invariants:
    - session_id is unique (no duplicate events for same session)
    - type is one of 'focus' or 'break'
    - duration_ms >= 0
    - completed_at is ISO8601 with timezone
    - created_at is server-generated
    """

    __tablename__ = "session_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, unique=True)
    type = Column(String(50), nullable=False)  # 'focus', 'break'
    duration_ms = Column(Integer, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "type": self.type,
            "duration_ms": self.duration_ms,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
