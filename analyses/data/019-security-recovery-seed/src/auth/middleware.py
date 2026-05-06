"""FastAPI dependency for protected endpoints — looks up the bearer
token, returns the Session if valid, raises 401 otherwise.

No rate limiting or anomaly detection at this layer. The request lands,
the dependency validates the session, the handler runs."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from src.auth.models import Session
from src.auth.service import AuthService


def make_session_dependency(auth: AuthService):
    """Factory for the FastAPI dependency. The dependency closes over
    a specific AuthService instance so the wiring stays explicit."""

    def _dep(authorization: str | None = Header(default=None)) -> Session:
        if authorization is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing Authorization header",
            )
        if not authorization.lower().startswith("bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header must be Bearer scheme",
            )
        token = authorization.split(" ", 1)[1].strip()
        session = auth.get_session(token)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="session expired or invalid",
            )
        return session

    return _dep
