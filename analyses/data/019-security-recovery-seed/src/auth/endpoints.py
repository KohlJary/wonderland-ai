"""FastAPI router for the auth surface — /login, /logout, /me.

This is the externally-reachable HTTP surface where credential checks
happen. It calls AuthService.login on POST /login and returns the
session token to the client.

No rate-limiting middleware is mounted ahead of this router. A caller
can hit POST /login arbitrarily quickly. See #ENG-471.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from src.auth.models import Session
from src.auth.service import AuthService


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_at: str


class MeResponse(BaseModel):
    user_id: str
    email: str


def make_router(auth: AuthService, session_dep) -> APIRouter:
    """Factory: returns an APIRouter wired to the supplied AuthService
    and session dependency."""
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post("/login", response_model=LoginResponse)
    def login(req: LoginRequest, request: Request) -> LoginResponse:
        source_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent")
        result = auth.login(
            email=str(req.email),
            password=req.password,
            source_ip=source_ip,
            user_agent=user_agent,
        )
        if not result.ok:
            # Single failure message regardless of reason — don't leak
            # whether the email exists.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid email or password",
            )
        session = result.session
        assert session is not None  # ok=True implies session is set
        return LoginResponse(
            token=session.token,
            expires_at=session.expires_at.isoformat(),
        )

    @router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
    def logout(session: Session = Depends(session_dep)) -> None:
        auth.logout(session.token)

    @router.get("/me", response_model=MeResponse)
    def me(session: Session = Depends(session_dep)) -> MeResponse:
        return MeResponse(user_id=session.user_id, email=session.user.email)

    return router
