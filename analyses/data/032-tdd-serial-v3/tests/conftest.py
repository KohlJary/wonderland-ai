"""Test fixtures — in-memory SQLite engine + a TestClient bound to
the FastAPI app with the engine swapped in. Lets every test get a
fresh DB without touching disk."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.db import get_db
from src.backend.main import app
from src.backend.models import Base


@pytest.fixture
def db_engine():
    """Fresh in-memory SQLite, schema created."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine) -> Iterator[Session]:
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, future=True)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_engine) -> Iterator[TestClient]:
    """TestClient with the in-memory DB wired through FastAPI's
    dependency-override mechanism."""
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, future=True)

    def _override_get_db() -> Iterator[Session]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
