"""AuthService — login, logout, session lookup. Backed by a SQLAlchemy
session factory. Includes rate limiting (per IP) and account lockout
(per email) as of the incident response in thread incident-response.
See src/auth/rate_limit.py for the control layer implementation."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session as DBSession

from src.auth.models import FailedAttempt, Session, User
from src.auth.passwords import verify_password
from src.auth.rate_limit import AccountLockout, RateLimitViolation, RateLimiter


@dataclass
class LoginResult:
    """Result of a login attempt.

    On success: ``ok=True`` and ``session`` carries the new Session
    row. On failure: ``ok=False`` and ``reason`` says why
    ('unknown_email', 'invalid_password', 'rate_limited', or 'account_locked').
    Callers should not differentiate credential failure reasons in
    user-facing error messages — that's a credential-enumeration leak
    the API layer guards against.

    When reason is 'rate_limited' or 'account_locked', retry_after_seconds
    contains the number of seconds the client should wait before retrying.
    """

    ok: bool
    reason: str | None = None
    session: Session | None = None
    retry_after_seconds: int | None = None


class AuthService:
    """Application-level auth orchestration. Holds the DB session
    factory and delegates per-call work to short transactions.

    Includes IP-based rate limiting and per-email account lockout
    to mitigate credential-stuffing attacks (see incident-response
    thread).
    """

    def __init__(
        self,
        db_session_factory,
        rate_limiter: RateLimiter | None = None,
        account_lockout: AccountLockout | None = None,
    ):
        self._db = db_session_factory
        self.rate_limiter = rate_limiter or RateLimiter(requests_per_minute=10, db_session_factory=db_session_factory)
        self.account_lockout = account_lockout or AccountLockout(failure_threshold=5, db_session_factory=db_session_factory)

    def login(
        self,
        email: str,
        password: str,
        source_ip: str,
        user_agent: str | None = None,
    ) -> LoginResult:
        """Attempt a login with email + password.

        On success: returns LoginResult with ok=True and a fresh
        Session row attached. On failure logs a FailedAttempt and
        returns ok=False with the failure reason.

        Rate limiting (per IP) and account lockout (per email) are
        checked before credential verification to prevent abuse.
        """
        normalized_email = email.strip().lower()

        # Check rate limit first (before any DB access).
        try:
            self.rate_limiter.check(source_ip)
        except RateLimitViolation as e:
            self._log_failure(
                None, normalized_email, "rate_limited", source_ip, user_agent
            )
            return LoginResult(
                ok=False,
                reason="rate_limited",
                retry_after_seconds=e.retry_after_seconds,
            )

        # Check account lockout.
        try:
            self.account_lockout.check(normalized_email)
        except RateLimitViolation as e:
            self._log_failure(
                None, normalized_email, "account_locked", source_ip, user_agent
            )
            return LoginResult(
                ok=False,
                reason="account_locked",
                retry_after_seconds=e.retry_after_seconds,
            )

        # Credentials check.
        with self._db() as db:
            user = db.query(User).filter(User.email == normalized_email).one_or_none()
            if user is None:
                self.account_lockout.record_failure(normalized_email)
                self._log_failure(db, normalized_email, "unknown_email", source_ip, user_agent)
                return LoginResult(ok=False, reason="unknown_email")
            if not verify_password(password, user.password_hash):
                self.account_lockout.record_failure(normalized_email)
                self._log_failure(db, normalized_email, "invalid_password", source_ip, user_agent)
                return LoginResult(ok=False, reason="invalid_password")

            # Success — create session and reset failure counters.
            session = Session.make(
                user_id=user.id, source_ip=source_ip, user_agent=user_agent
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            # Successful login resets the lockout counter for this email.
            self.account_lockout.record_success(normalized_email)

            return LoginResult(ok=True, session=session)

    def logout(self, token: str) -> bool:
        """Invalidate a session token and return True if it existed,
        False if the token was not found.

        Note: this does NOT rate-limit or restrict the logout path —
        logout should always be available regardless of account state.
        """
        with self._db() as db:
            session = db.query(Session).filter(Session.token == token).one_or_none()
            if session is None:
                return False
            db.delete(session)
            db.commit()
            return True

    def get_session(self, token: str) -> Session | None:
        """Look up a session by token. Returns the Session row if valid,
        None if the token is unknown or the session has expired.

        This is read-only and does not interact with rate limiting."""
        with self._db() as db:
            session = (
                db.query(Session)
                .filter(Session.token == token)
                .filter(Session.is_valid())
                .one_or_none()
            )
            return session

    @staticmethod
    def _log_failure(
        db: DBSession | None,
        email: str,
        reason: str,
        source_ip: str,
        user_agent: str | None,
    ) -> None:
        """Log a failed attempt to the FailedAttempt table.

        If db is None (rate-limit or lockout check before DB access),
        this is a no-op. The rate-limit and lockout checks themselves
        are the primary defense; logging them would require creating
        a new session, which adds latency during an active attack.
        For incident response, the absence of these logs is acceptable;
        the IP is already rate-limited by the RateLimiter/AccountLockout
        in-memory state.
        """
        if db is None:
            # Rate-limit or lockout violation — don't log (would require
            # creating a new DB session and slow down the response).
            return

        attempt = FailedAttempt(
            email=email,
            source_ip=source_ip,
            user_agent=user_agent,
            reason=reason,
        )
        db.add(attempt)
        db.commit()
