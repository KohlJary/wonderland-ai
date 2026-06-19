"""Pytest configuration and fixtures for backend tests."""
import os
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient

# Set test database URL
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from src.backend.main import app
from src.backend.dependencies import get_db
from src.backend.database import Base, User, PartnerProfile, WeatherCache, NewsCache
from src.backend.auth import hash_password


@pytest_asyncio.fixture
async def db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def override_get_db(db_session):
    """Override get_db dependency for testing."""
    def _override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_db):
    """Create a test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def authenticated_user(db_session) -> User:
    """Create an authenticated user for testing."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_with_partner_profile(db_session, authenticated_user) -> tuple[User, PartnerProfile]:
    """Create a user with a partner profile."""
    partner = PartnerProfile(
        user_id=authenticated_user.id,
        city="Vienna",
        country="Austria",
        timezone="Europe/Vienna",
        latitude=48.2082,
        longitude=16.3738,
    )
    db_session.add(partner)
    await db_session.commit()
    await db_session.refresh(authenticated_user)
    await db_session.refresh(partner)
    return authenticated_user, partner


@pytest_asyncio.fixture
async def user_with_failed_weather_cache(db_session, user_with_partner_profile) -> tuple[User, PartnerProfile, WeatherCache]:
    """
    Create a user with a partner profile and a weather cache entry that 
    was never successfully populated (simulating an API failure before any successful fetch).
    
    This is the key test scenario: cache row exists but last_successful_fetch_at is None.
    """
    user, partner = user_with_partner_profile
    
    # Create a weather cache entry that was attempted but never succeeded
    # (e.g., Open-Meteo was down when polling job ran)
    from datetime import datetime
    now = datetime.utcnow()
    cache = WeatherCache(
        user_id=user.id,
        temperature_f=None,
        condition_code=None,
        condition_description=None,
        cached_at=now,  # Row exists, but data was never fetched
        last_fetch_attempt_at=None,
        last_successful_fetch_at=None,  # This is the key: never successfully fetched
    )
    db_session.add(cache)
    await db_session.commit()
    await db_session.refresh(cache)
    
    return user, partner, cache
