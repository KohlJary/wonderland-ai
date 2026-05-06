"""Rate limiting and account lockout for auth endpoints.

Provides two control layers:
1. IP-based rate limiting (failed attempts per source IP within a rolling window)
2. Email-based account lockout (failed attempts per email within a rolling window)

Both use the FailedAttempt table as the source of truth, querying for attempts
within the configured window. This provides:
- Durability across service restarts
- Observability (all rate-limit decisions are queryable)
- Centralized enforcement (shared across service instances)

The tradeoff is database load during attacks; mitigated by indexed lookups on
(source_ip, occurred_at) and (email, occurred_at).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Callable

from sqlalchemy.orm import Session as DBSession

from src.auth.models import FailedAttempt


class RateLimitStatus(Enum):
    """Possible outcomes of a rate-limit check."""

    ALLOWED = "allowed"
    IP_THROTTLED = "ip_throttled"
    ACCOUNT_LOCKED = "account_locked"


class RateLimitResult:
    """Result of a rate-limit check."""

    def __init__(self, status: RateLimitStatus, retry_after_seconds: int | None = None):
        self.status = status
        self.retry_after_seconds = retry_after_seconds


class RateLimitViolation(Exception):
    """Raised when a rate-limit or lockout threshold is exceeded."""

    def __init__(self, status: RateLimitStatus, retry_after_seconds: int | None = None):
        self.status = status
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit violation: {status.value}")


class RateLimiter:
    """Stateless rate limiter backed by FailedAttempt table.

    Queries the table for failures within configured windows and enforces
    thresholds. No in-memory state; all lookups are against the database.
    """

    # Per-IP rate limit: 10 failed attempts in 15 minutes (per Queen ruling 001)
    IP_MAX_FAILURES = 10
    IP_WINDOW_MINUTES = 15

    def __init__(self, requests_per_minute: int = 10, db_session_factory: Callable | None = None):
        """Initialize the rate limiter.

        Args:
            requests_per_minute: max failed attempts before rate-limiting (deprecated; kept for compatibility)
            db_session_factory: SQLAlchemy session factory (optional)
        """
        self.ip_max_failures = requests_per_minute or self.IP_MAX_FAILURES
        self.ip_window_minutes = self.IP_WINDOW_MINUTES
        self._db = db_session_factory

    def check(self, source_ip: str) -> None:
        """Check if a login attempt is rate-limited by IP.

        Raises RateLimitViolation if the IP has exceeded the threshold.

        Args:
            source_ip: client source IP address

        Raises:
            RateLimitViolation: if rate limit is exceeded
        """
        if self._db is None:
            # No DB session factory provided; skip rate limiting.
            return

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=self.ip_window_minutes)

        with self._db() as db:
            failure_count = (
                db.query(FailedAttempt)
                .filter(
                    FailedAttempt.source_ip == source_ip,
                    FailedAttempt.occurred_at >= window_start,
                )
                .count()
            )

        if failure_count >= self.ip_max_failures:
            # Calculate when the window will expire
            oldest_failure = self._get_oldest_failure_for_ip(source_ip)
            if oldest_failure:
                window_expires = oldest_failure + timedelta(minutes=self.ip_window_minutes)
                retry_after = max(0, int((window_expires - now).total_seconds()))
            else:
                retry_after = self.ip_window_minutes * 60

            raise RateLimitViolation(
                RateLimitStatus.IP_THROTTLED,
                retry_after_seconds=retry_after,
            )

    def get_ip_failure_count(self, source_ip: str) -> int:
        """Convenience: get current failure count for an IP (within the window)."""
        if self._db is None:
            return 0

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=self.ip_window_minutes)

        with self._db() as db:
            return (
                db.query(FailedAttempt)
                .filter(
                    FailedAttempt.source_ip == source_ip,
                    FailedAttempt.occurred_at >= window_start,
                )
                .count()
            )

    def _get_oldest_failure_for_ip(self, source_ip: str) -> datetime | None:
        """Get the oldest failure timestamp for an IP (within the window)."""
        if self._db is None:
            return None

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=self.ip_window_minutes)

        with self._db() as db:
            result = (
                db.query(FailedAttempt.occurred_at)
                .filter(
                    FailedAttempt.source_ip == source_ip,
                    FailedAttempt.occurred_at >= window_start,
                )
                .order_by(FailedAttempt.occurred_at)
                .first()
            )
            return result[0] if result else None


class AccountLockout:
    """Per-email account lockout based on failed login attempts.

    Tracks failures per email and locks the account after a threshold
    is exceeded within a time window.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        lockout_duration: timedelta = timedelta(minutes=30),
        db_session_factory: Callable | None = None,
    ):
        """Initialize account lockout.

        Args:
            failure_threshold: number of failures before lockout
            lockout_duration: how long the account stays locked
            db_session_factory: SQLAlchemy session factory (optional)
        """
        self.failure_threshold = failure_threshold
        self.lockout_duration = lockout_duration
        self._db = db_session_factory
        # In-memory tracking for quick checks (complemented by DB for durability)
        self._failure_counts: dict[str, int] = {}
        self._failure_times: dict[str, list[datetime]] = {}

    def check(self, email: str) -> None:
        """Check if an email is locked out.

        Raises RateLimitViolation if the email has exceeded the failure threshold.

        Args:
            email: normalized email address

        Raises:
            RateLimitViolation: if account is locked
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=int(self.lockout_duration.total_seconds()))

        # Check in-memory state first (fast path)
        if email in self._failure_counts:
            if self._failure_counts[email] >= self.failure_threshold:
                # Check if the lock is still active
                if self._failure_times.get(email) and self._failure_times[email][0] >= window_start:
                    window_expires = self._failure_times[email][0] + self.lockout_duration
                    retry_after = max(0, int((window_expires - now).total_seconds()))
                    raise RateLimitViolation(
                        RateLimitStatus.ACCOUNT_LOCKED,
                        retry_after_seconds=retry_after,
                    )
                else:
                    # Window expired; clear the in-memory state
                    self._failure_counts[email] = 0
                    self._failure_times[email] = []

        # Optionally check DB as well (if session factory is provided)
        if self._db is not None:
            with self._db() as db:
                failure_count = (
                    db.query(FailedAttempt)
                    .filter(
                        FailedAttempt.email == email,
                        FailedAttempt.occurred_at >= window_start,
                    )
                    .count()
                )

            if failure_count >= self.failure_threshold:
                oldest_failure = self._get_oldest_failure_for_email(email)
                if oldest_failure:
                    window_expires = oldest_failure + self.lockout_duration
                    retry_after = max(0, int((window_expires - now).total_seconds()))
                    raise RateLimitViolation(
                        RateLimitStatus.ACCOUNT_LOCKED,
                        retry_after_seconds=retry_after,
                    )

    def record_failure(self, email: str) -> None:
        """Record a failed login attempt for an email.

        Args:
            email: normalized email address
        """
        now = datetime.now(timezone.utc)

        # Update in-memory state
        if email not in self._failure_counts:
            self._failure_counts[email] = 0
            self._failure_times[email] = []

        self._failure_counts[email] += 1
        self._failure_times[email].append(now)

        # Keep only recent failures within the window
        window_start = now - timedelta(seconds=int(self.lockout_duration.total_seconds()))
        self._failure_times[email] = [t for t in self._failure_times[email] if t >= window_start]
        self._failure_counts[email] = len(self._failure_times[email])

    def record_success(self, email: str) -> None:
        """Record a successful login for an email; resets the failure counter.

        Args:
            email: normalized email address
        """
        # Clear in-memory state for this email
        if email in self._failure_counts:
            self._failure_counts[email] = 0
            self._failure_times[email] = []

    def is_account_locked(self, email: str) -> bool:
        """Convenience: check if an account is locked.

        Returns True if the email has hit the account-lockout threshold.
        """
        try:
            self.check(email)
            return False
        except RateLimitViolation:
            return True

    def _get_oldest_failure_for_email(self, email: str) -> datetime | None:
        """Get the oldest failure timestamp for an email (within the window)."""
        if self._db is None:
            return None

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=int(self.lockout_duration.total_seconds()))

        with self._db() as db:
            result = (
                db.query(FailedAttempt.occurred_at)
                .filter(
                    FailedAttempt.email == email,
                    FailedAttempt.occurred_at >= window_start,
                )
                .order_by(FailedAttempt.occurred_at)
                .first()
            )
            return result[0] if result else None
