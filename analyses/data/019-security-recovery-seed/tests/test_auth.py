"""Baseline auth tests — login success/failure, session validity,
logout. Intentionally does NOT cover rate limiting or lockout because
those primitives aren't built yet (see #ENG-471)."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth.models import Base, FailedAttempt, User
from src.auth.passwords import hash_password
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


# Note: there is intentionally no test_login_rate_limited test, because
# /login has no rate limit yet. See #ENG-471 for the deferred work.
