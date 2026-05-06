"""AuthService — login, logout, session lookup. Backed by a SQLAlchemy
session factory. No rate limiting and no automatic lockout (see
#ENG-471 for the open thread on those)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from src.auth.models import FailedAttempt, Session, User
from src.auth.passwords import verify_password


@dataclass
class LoginResult:
    """Outcome of an AuthService.login call.

    On success: ``ok=True`` and ``session`` carries the new Session
    row. On failure: ``ok=False`` and ``reason`` says why
    ('unknown_email' or 'invalid_password'). Callers should not
    differentiate the two reasons in user-facing error messages —
    that's a credential-enumeration leak the API layer guards
    against.
    """

    ok: bool
    reason: str = ""
    session: Session | None = None


class AuthService:
    """Application-level auth orchestration. Holds the DB session
    factory and delegates per-call work to short transactions."""

    def __init__(self, db_session_factory):
        self._db = db_session_factory

    def login(
        self,
        email: str,
        password: str,
        source_ip: str,
        user_agent: str | None = None,
    ) -> LoginResult:
        """Attempt to authenticate (email, password).

        On success returns a LoginResult with ok=True and the new
        Session row attached. On failure logs a FailedAttempt and
        returns ok=False with the failure reason.

        NOTE: there is no rate limit here. A caller can call this
        method an unbounded number of times — the failure path only
        writes the FailedAttempt row. See #ENG-471.
        """
        normalized_email = email.strip().lower()
        with self._db() as db:
            user = db.query(User).filter(User.email == normalized_email).one_or_none()
            if user is None:
                self._log_failure(db, normalized_email, "unknown_email", source_ip, user_agent)
                return LoginResult(ok=False, reason="unknown_email")
            if not verify_password(password, user.password_hash):
                self._log_failure(db, normalized_email, "invalid_password", source_ip, user_agent)
                return LoginResult(ok=False, reason="invalid_password")
            session = Session.make(
                user_id=user.id, source_ip=source_ip, user_agent=user_agent
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return LoginResult(ok=True, session=session)

    def logout(self, token: str) -> bool:
        """Invalidate a session token. Returns True if the session
        existed (and was deleted), False otherwise."""
        with self._db() as db:
            session = db.query(Session).filter(Session.token == token).one_or_none()
            if session is None:
                return False
            db.delete(session)
            db.commit()
            return True

    def get_session(self, token: str) -> Session | None:
        """Look up an active (non-expired) session by token. Returns
        None for unknown or expired tokens — callers treat both the
        same way (re-auth required)."""
        with self._db() as db:
            session = db.query(Session).filter(Session.token == token).one_or_none()
            if session is None or session.is_expired():
                return None
            session.last_seen_at = datetime.now(timezone.utc)
            db.add(session)
            db.commit()
            db.refresh(session)
            return session

    @staticmethod
    def _log_failure(
        db: DBSession,
        email: str,
        reason: str,
        source_ip: str,
        user_agent: str | None,
    ) -> None:
        attempt = FailedAttempt(
            email=email,
            source_ip=source_ip,
            user_agent=user_agent,
            reason=reason,
        )
        db.add(attempt)
        db.commit()
