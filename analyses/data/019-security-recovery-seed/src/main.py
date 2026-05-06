"""FastAPI app wiring — creates the engine, the AuthService, the
session dependency, and mounts the auth router."""

from __future__ import annotations

import os

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.auth.endpoints import make_router
from src.auth.middleware import make_session_dependency
from src.auth.models import Base
from src.auth.service import AuthService


def create_app() -> FastAPI:
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./auth.db")
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)

    auth = AuthService(db_session_factory=SessionLocal)
    session_dep = make_session_dependency(auth)
    router = make_router(auth, session_dep)

    app = FastAPI(title="auth-service", version="0.1.0")
    app.include_router(router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
