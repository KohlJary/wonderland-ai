"""SQLAlchemy engine + session factory.

SQLite by default (good enough for development); set DATABASE_URL to
swap. The `get_db` FastAPI dependency yields a Session and ensures
cleanup."""

from __future__ import annotations

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./app.db")

# check_same_thread=False is needed for SQLite when used with
# FastAPI's threadpool execution model. For Postgres etc. this kwarg
# is ignored.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI dependency — yields a Session, closes it after the
    request handler returns."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
