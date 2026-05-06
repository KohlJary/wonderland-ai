"""SQLAlchemy models for auth — User, Session, FailedAttempt."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid4().hex


class User(Base):
    """A registered account.

    Email is the login identity (lowercased on insert). password_hash is
    bcrypt-encoded. created_at and updated_at are server-stamped. No
    lockout state is stored on the user row — failed attempts live in
    the FailedAttempt table.
    """

    __tablename__ = "users"

    id = Column(String(32), primary_key=True, default=_new_id)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    sessions = relationship("Session", back_populates="user", cascade="all,delete")

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r}>"


class Session(Base):
    """An active authenticated session.

    token is the bearer credential the client carries (cookie or
    Authorization header). expires_at is the absolute UTC timestamp
    after which the session is invalid; refresh extends it.
    """

    __tablename__ = "sessions"

    token = Column(String(64), primary_key=True, default=_new_id)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    source_ip = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)

    user = relationship("User", back_populates="sessions")

    def is_expired(self) -> bool:
        return _utcnow() >= self.expires_at

    @classmethod
    def make(
        cls,
        user_id: str,
        ttl: timedelta = timedelta(hours=24),
        source_ip: str | None = None,
        user_agent: str | None = None,
    ) -> Session:
        return cls(
            token=_new_id(),
            user_id=user_id,
            expires_at=_utcnow() + ttl,
            source_ip=source_ip,
            user_agent=user_agent,
        )


class FailedAttempt(Base):
    """A failed login attempt.

    Logged for forensic visibility — see also #ENG-471 (rate limiting
    + lockout policy, deferred). Currently this table is write-only
    from /login; nothing reads it to enforce limits yet.
    """

    __tablename__ = "failed_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, index=True)
    source_ip = Column(String(64), nullable=False, index=True)
    user_agent = Column(String(512), nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reason = Column(String(64), nullable=False)  # 'invalid_password' | 'unknown_email'

    __table_args__ = (
        Index("ix_failed_attempts_email_time", "email", "occurred_at"),
        Index("ix_failed_attempts_ip_time", "source_ip", "occurred_at"),
    )
