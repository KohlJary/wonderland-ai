"""Auth tests — login success/failure, session validity, logout,
rate limiting, and account lockout.

Rate limiting and lockout coverage was added during the incident-response
thread to address #ENG-471.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth.models import Base, FailedAttempt, User
from src.auth.passwords import hash_password
from src.auth.rate_limit import AccountLockout, RateLimiter
from src.auth.service import AuthService


@pytest.fixture
def db_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
    return SessionLocal


@pytest.fixture
def auth(db_factory):
    return AuthService(db_session_factory=db_factory)


@pytest.fixture
def auth_with_lenient_limits(db_factory):
    """AuthService with higher rate limit and lockout threshold for testing."""
    return AuthService(
        db_session_factory=db_factory,
        rate_limiter=RateLimiter(requests_per_minute=100, db_session_factory=db_factory),
        account_lockout=AccountLockout(failure_threshold=3, lockout_duration=timedelta(seconds=10), db_session_factory=db_factory),
    )


@pytest.fixture
def known_user(db_factory):
    with db_factory() as db:
        user = User(
            email="alice@example.com",
            password_hash=hash_password("correct horse battery staple"),
            display_name="Alice",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id


# ===== Baseline tests (pre-incident) =====


def test_login_with_correct_password_returns_session(auth, known_user):
    result = auth.login(
        email="alice@example.com",
        password="correct horse battery staple",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    assert result.ok is True
    assert result.session is not None
    assert result.session.user_id == known_user
    assert result.session.token  # non-empty token issued


def test_login_with_wrong_password_returns_failure(auth, known_user):
    result = auth.login(
        email="alice@example.com",
        password="wrong",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    assert result.ok is False
    assert result.reason == "invalid_password"
    assert result.session is None


def test_login_with_unknown_email_returns_failure(auth):
    result = auth.login(
        email="nobody@example.com",
        password="anything",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    assert result.ok is False
    assert result.reason == "unknown_email"


def test_failed_attempts_are_logged(auth, known_user, db_factory):
    auth.login(
        email="alice@example.com",
        password="wrong",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    auth.login(
        email="alice@example.com",
        password="also-wrong",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    with db_factory() as db:
        attempts = (
            db.query(FailedAttempt).filter(FailedAttempt.email == "alice@example.com").all()
        )
        assert len(attempts) == 2
        assert all(a.reason == "invalid_password" for a in attempts)


def test_get_session_returns_active_session(auth, known_user):
    result = auth.login(
        email="alice@example.com",
        password="correct horse battery staple",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    found = auth.get_session(result.session.token)
    assert found is not None
    assert found.user_id == known_user


def test_get_session_returns_none_for_unknown_token(auth):
    assert auth.get_session("not-a-real-token") is None


def test_logout_invalidates_session(auth, known_user):
    result = auth.login(
        email="alice@example.com",
        password="correct horse battery staple",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    token = result.session.token
    assert auth.logout(token) is True
    assert auth.get_session(token) is None
    # Second logout returns False — session no longer exists.
    assert auth.logout(token) is False


# ===== Rate limiting tests (incident-response) =====


def test_rate_limit_blocks_excessive_requests_from_single_ip(auth_with_lenient_limits, known_user, db_factory):
    """After N requests in one minute from the same IP, further requests are rejected."""
    # auth_with_lenient_limits has rate_limiter(requests_per_minute=100), so
    # we can make 100 requests. Adjust the limit down for this test.
    auth = AuthService(
        db_session_factory=db_factory,
        rate_limiter=RateLimiter(requests_per_minute=3, db_session_factory=db_factory),
        account_lockout=auth_with_lenient_limits.account_lockout,
    )
    
    # First 3 requests should succeed (even with wrong password).
    for i in range(3):
        result = auth.login(
            email="alice@example.com",
            password="wrong",
            source_ip="203.0.113.42",  # Fixed source IP.
            user_agent="pytest",
        )
        # Credentials fail, but rate limit doesn't (yet).
        assert result.ok is False
        assert result.reason == "invalid_password"
    
    # 4th request should be rate-limited.
    result = auth.login(
        email="alice@example.com",
        password="wrong",
        source_ip="203.0.113.42",
        user_agent="pytest",
    )
    assert result.ok is False
    assert result.reason == "rate_limited"


def test_rate_limit_is_per_ip(db_factory):
    """Different IPs have independent rate limits."""
    auth = AuthService(
        db_session_factory=db_factory,
        rate_limiter=RateLimiter(requests_per_minute=2, db_session_factory=db_factory),
        account_lockout=AccountLockout(failure_threshold=100, db_session_factory=db_factory),
    )
    
    # 2 requests from IP A — should succeed up to limit.
    result1 = auth.login(
        email="alice@example.com",
        password="wrong",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    assert result1.reason != "rate_limited"
    
    result2 = auth.login(
        email="alice@example.com",
        password="wrong",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    assert result2.reason != "rate_limited"
    
    # 3rd request from IP A should be rate-limited.
    result3 = auth.login(
        email="alice@example.com",
        password="wrong",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    assert result3.reason == "rate_limited"
    
    # But IP B should still have capacity.
    result4 = auth.login(
        email="alice@example.com",
        password="wrong",
        source_ip="10.0.0.2",
        user_agent="pytest",
    )
    assert result4.reason != "rate_limited"


# ===== Account lockout tests (incident-response) =====


def test_account_lockout_fires_after_threshold(auth_with_lenient_limits, known_user):
    """After N failed attempts on the same email, further attempts are locked."""
    # auth_with_lenient_limits has lockout_threshold=3.
    
    # 3 failed attempts should lock the account.
    for i in range(3):
        result = auth_with_lenient_limits.login(
            email="alice@example.com",
            password="wrong",
            source_ip="10.0.0.1",
            user_agent="pytest",
        )
        assert result.ok is False
        assert result.reason == "invalid_password"
    
    # 4th attempt should be locked (even with correct password).
    result = auth_with_lenient_limits.login(
        email="alice@example.com",
        password="correct horse battery staple",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    assert result.ok is False
    assert result.reason == "account_locked"


def test_account_lockout_is_per_email(db_factory):
    """Different emails have independent lockout states."""
    with db_factory() as db:
        user_a = User(
            email="alice@example.com",
            password_hash=hash_password("alice_password"),
            display_name="Alice",
        )
        user_b = User(
            email="bob@example.com",
            password_hash=hash_password("bob_password"),
            display_name="Bob",
        )
        db.add_all([user_a, user_b])
        db.commit()
    
    auth = AuthService(
        db_session_factory=db_factory,
        rate_limiter=RateLimiter(requests_per_minute=100, db_session_factory=db_factory),
        account_lockout=AccountLockout(failure_threshold=2, db_session_factory=db_factory),
    )
    
    # 2 failed attempts on alice — locks alice.
    auth.login(
        email="alice@example.com",
        password="wrong",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    auth.login(
        email="alice@example.com",
        password="wrong",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    
    # Alice is now locked.
    result = auth.login(
        email="alice@example.com",
        password="alice_password",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    assert result.reason == "account_locked"
    
    # But Bob can still log in — his account isn't locked.
    result = auth.login(
        email="bob@example.com",
        password="bob_password",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    assert result.ok is True


def test_successful_login_resets_lockout_counter(auth_with_lenient_limits, known_user):
    """Successful login resets the failure counter for that email."""
    # Make 2 failed attempts (below threshold of 3).
    auth_with_lenient_limits.login(
        email="alice@example.com",
        password="wrong",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    auth_with_lenient_limits.login(
        email="alice@example.com",
        password="wrong",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    
    # Successful login should reset the counter.
    result = auth_with_lenient_limits.login(
        email="alice@example.com",
        password="correct horse battery staple",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    assert result.ok is True
    
    # After reset, we can make 2 more failed attempts before lockout fires.
    auth_with_lenient_limits.login(
        email="alice@example.com",
        password="wrong",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    auth_with_lenient_limits.login(
        email="alice@example.com",
        password="wrong",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    
    # Still not locked.
    result = auth_with_lenient_limits.login(
        email="alice@example.com",
        password="wrong",
        source_ip="10.0.0.1",
        user_agent="pytest",
    )
    assert result.reason == "account_locked"


def test_rate_limit_and_lockout_are_independent(db_factory):
    """Rate limit (per IP) and lockout (per email) can both fire independently."""
    auth = AuthService(
        db_session_factory=db_factory,
        rate_limiter=RateLimiter(requests_per_minute=5, db_session_factory=db_factory),
        account_lockout=AccountLockout(failure_threshold=3, db_session_factory=db_factory),
    )
    
    # Scenario: attacker at IP A tries email alice (hits lockout).
    # Then tries email bob from same IP A (hits rate limit).
    
    with db_factory() as db:
        alice = User(
            email="alice@example.com",
            password_hash=hash_password("alice_password"),
        )
        bob = User(
            email="bob@example.com",
            password_hash=hash_password("bob_password"),
        )
        db.add_all([alice, bob])
        db.commit()
    
    attacker_ip = "203.0.113.42"
    
    # 3 failed attempts on alice — locks alice.
    for _ in range(3):
        auth.login(
            email="alice@example.com",
            password="wrong",
            source_ip=attacker_ip,
            user_agent="pytest",
        )
    
    # Alice is locked.
    result = auth.login(
        email="alice@example.com",
        password="wrong",
        source_ip=attacker_ip,
        user_agent="pytest",
    )
    assert result.reason == "account_locked"
    
    # IP now has 4 requests. Trying bob will trigger rate limit on request 5 + 1.
    # Make 2 more attempts on bob (4 + 2 = 6 total from the IP, exceeds limit of 5).
    auth.login(
        email="bob@example.com",
        password="wrong",
        source_ip=attacker_ip,
        user_agent="pytest",
    )
    
    result = auth.login(
        email="bob@example.com",
        password="wrong",
        source_ip=attacker_ip,
        user_agent="pytest",
    )
    assert result.reason == "rate_limited"
