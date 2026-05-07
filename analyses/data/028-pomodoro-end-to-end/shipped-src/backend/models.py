"""SQLAlchemy models for Focus Session tracking."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Integer, String, Boolean, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# State enums for clarity
class SessionState(str, PyEnum):
    """Session states."""
    ACTIVE = "active"
    COMPLETED = "completed"


class BreakState(str, PyEnum):
    """Break states."""
    ACTIVE = "active"
    SKIPPED = "skipped"
    COMPLETED = "completed"


# Make them accessible as both enum and string constants for backward compatibility
SessionState.active = "active"
SessionState.completed = "completed"
BreakState.active = "active"
BreakState.skipped = "skipped"
BreakState.completed = "completed"


class User(Base):
    """User profile with tracking metadata."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # launch_date: the timestamp of the first session creation
    launch_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def to_dict(self) -> dict:
        # Compute days_tracked server-side
        now = datetime.now(timezone.utc)
        days_tracked = 0
        if self.launch_date:
            delta = now - self.launch_date
            days_tracked = delta.days

        return {
            "id": self.id,
            "launch_date": (
                self.launch_date.isoformat() if self.launch_date else None
            ),
            "days_tracked": days_tracked,
        }


class UserSettings(Base):
    """User customizable settings for session/break durations."""

    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # Single user for now
    session_duration_minutes = Column(Integer, nullable=False, default=25)
    break_duration_minutes = Column(Integer, nullable=False, default=5)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "session_duration_minutes": self.session_duration_minutes,
            "break_duration_minutes": self.break_duration_minutes,
        }


class Session(Base):
    """Focus session tracking."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # Single user for now
    state = Column(String(50), nullable=False, default="active")  # active, completed
    duration_minutes = Column(Integer, nullable=False, default=25)
    start_time = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def to_dict(self) -> dict:
        now = datetime.now(timezone.utc)
        remaining_seconds = self.duration_minutes * 60

        if self.state == "active":
            elapsed = (now - self.start_time).total_seconds()
            remaining_seconds = max(0, self.duration_minutes * 60 - int(elapsed))

        return {
            "id": self.id,
            "state": self.state,
            "duration_minutes": self.duration_minutes,
            "start_time": self.start_time.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "remaining_seconds": remaining_seconds,
        }


class Break(Base):
    """Break period after a session."""

    __tablename__ = "breaks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # Single user for now
    session_id = Column(Integer, nullable=False)  # Associated session
    state = Column(String(50), nullable=False, default="active")  # active, skipped, completed
    duration_minutes = Column(Integer, nullable=False, default=5)
    start_time = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def to_dict(self) -> dict:
        now = datetime.now(timezone.utc)
        remaining_seconds = self.duration_minutes * 60

        if self.state == "active":
            elapsed = (now - self.start_time).total_seconds()
            remaining_seconds = max(0, self.duration_minutes * 60 - int(elapsed))

        return {
            "id": self.id,
            "state": self.state,
            "duration_minutes": self.duration_minutes,
            "start_time": self.start_time.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "remaining_seconds": remaining_seconds,
            "skip_available": self.state == "active",
        }
