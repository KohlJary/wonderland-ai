"""SQLAlchemy models.

Session models for Pomodoro timer feature:
- Session: in-progress or paused sessions (focus/break)
- SessionLog: persists completed focus/break sessions
- UserSettings: user configuration (backend stub for v1, client-side localStorage primary)
  
Replaces the skeleton HelloMessage template.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    Integer,
    String,
    func,
    Index,
    UniqueConstraint,
    Boolean,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SessionType(str, Enum):
    """Valid session types."""
    FOCUS = "focus"
    BREAK = "break"


class SessionStatus(str, Enum):
    """Status of an in-progress session."""
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class Session(Base):
    """In-progress or paused focus/break session.
    
    Invariants:
    - Each session has exactly one type (focus or break)
    - duration_seconds >= 60 and <= 7200 (focus) or <= 1800 (break)
    - created_at must be ISO8601 timestamp and not in the future
    - status is one of running, paused, completed, skipped
    """

    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)  # UUID as string
    user_id = Column(String(255), nullable=False, index=True)
    type = Column(SQLEnum(SessionType), nullable=False)
    status = Column(SQLEnum(SessionStatus), nullable=False, default=SessionStatus.RUNNING)
    duration_seconds = Column(Integer, nullable=False)  # Configured duration
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Index for fast retrieval of active sessions
    __table_args__ = (
        Index("ix_sessions_user_active", "user_id", "status"),
    )

    def to_dict(self) -> dict:
        """Serialize session to dict for API response."""
        return {
            "id": self.id,
            "type": self.type.value,
            "status": self.status.value,
            "duration_seconds": self.duration_seconds,
            "created_at": (
                self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat()
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else datetime.now(timezone.utc).isoformat()
            ),
        }


class SessionLog(Base):
    """Persistent record of completed focus/break sessions.
    
    Invariants:
    - Each session has exactly one type (focus or break)
    - duration_actual <= duration_configured + 5% (timer drift tolerance)
    - completed_at must be ISO8601 timestamp and not in the future
    - Idempotent on duplicate submissions (same user, type, completed_at)
    """

    __tablename__ = "session_logs"

    id = Column(String(36), primary_key=True)  # UUID as string
    user_id = Column(String(255), nullable=False, index=True)  # Future: foreign key to users
    type = Column(SQLEnum(SessionType), nullable=False)
    duration_configured_seconds = Column(Integer, nullable=False)
    duration_actual_seconds = Column(Integer, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Composite index for idempotency: (user_id, type, completed_at)
    __table_args__ = (
        Index("ix_session_logs_idempotency", "user_id", "type", "completed_at"),
        UniqueConstraint("user_id", "type", "completed_at", name="uq_session_logs_idempotency"),
    )

    def to_dict(self) -> dict:
        return {
            "session_id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "duration_configured_seconds": self.duration_configured_seconds,
            "duration_actual_seconds": self.duration_actual_seconds,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else datetime.now(timezone.utc).isoformat()
            ),
            "created_at": (
                self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat()
            ),
        }


class UserSettings(Base):
    """User configuration.
    
    v1: Backend stub only. Settings are primarily client-side (localStorage).
    Backend persists for future reference but does not enforce or serve them
    in the session-creation logic (client passes configured durations with each request).
    
    Invariants:
    - focus_duration_seconds: range [60, 7200]
    - break_duration_seconds: range [60, 1800]
    - sound_enabled: boolean
    """

    __tablename__ = "user_settings"

    user_id = Column(String(255), primary_key=True)
    focus_duration_seconds = Column(Integer, nullable=False, default=1500)  # 25 min default
    break_duration_seconds = Column(Integer, nullable=False, default=300)   # 5 min default
    sound_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "focus_duration_seconds": self.focus_duration_seconds,
            "break_duration_seconds": self.break_duration_seconds,
            "sound_enabled": self.sound_enabled,
        }
