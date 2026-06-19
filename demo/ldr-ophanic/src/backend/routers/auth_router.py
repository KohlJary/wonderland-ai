"""
Authentication endpoints: signup, signin, and current-user bootstrap.

These endpoints are the entry points for the session middleware.
POST /auth/signup and /auth/signin set the signed session cookie.
GET /auth/me is the client's bootstrap call to validate session + get user info.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.database import User
from src.backend.dependencies import get_current_user, get_db
from src.backend.auth import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


# Request/response schemas
class SignupRequest(BaseModel):
    email: EmailStr
    password: str  # Frontend validates length >= 8; backend enforces min 8


class SigninRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Endpoints

@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(
    req: SignupRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Sign up with email + password.
    
    **Contract:**
    - Accepts POST /auth/signup { email, password }
    - Validates email format (handled by EmailStr)
    - Validates password is at least 8 characters (handled by frontend; backend enforces)
    - Checks email is not already registered (returns 409 if exists)
    - Hashes password with bcrypt (cost 12)
    - Stores User record in database
    - Sets signed session cookie in response
    - Returns 201 + User {id, email, created_at}
    
    **Invariants enforced:**
    - email is unique (database UNIQUE constraint)
    - password_hash is never exposed
    - user_id is stable after creation
    - password is never logged
    
    **Failure modes handled:**
    - Email already exists: HTTPException(409 Conflict)
    - Password too short: HTTPException(400 Bad Request)
    - Database error: exception propagates (500)
    """
    # Validate password length
    if len(req.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )
    
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == req.email.lower())
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    
    # Hash password and create user
    password_hash = hash_password(req.password)
    user = User(
        email=req.email.lower(),
        password_hash=password_hash,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Set signed session cookie
    request.session["user_id"] = user.id
    
    return UserResponse.model_validate(user)


@router.post("/signin", response_model=UserResponse, status_code=200)
async def signin(
    req: SigninRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Sign in with email + password.
    
    **Contract:**
    - Accepts POST /auth/signin { email, password }
    - Looks up user by email (case-insensitive)
    - Verifies password against stored hash (constant-time)
    - Sets signed session cookie in response
    - Returns 200 + User {id, email, created_at}
    
    **Invariants enforced:**
    - password verification is constant-time (no timing attacks)
    - password is never logged
    - session is established immediately on successful verification
    
    **Failure modes handled:**
    - Email not found: HTTPException(401 Unauthorized)
    - Password incorrect: HTTPException(401 Unauthorized)
    - Database error: exception propagates (500)
    
    Note: Email-not-found and password-incorrect both return 401 to prevent
    enumeration attacks (attacker can't tell which email is registered).
    """
    # Look up user by email (case-insensitive)
    result = await db.execute(
        select(User).where(User.email == req.email.lower())
    )
    user = result.scalar_one_or_none()
    
    # Check password (do this even if user not found to avoid timing attack)
    password_valid = False
    if user:
        password_valid = verify_password(req.password, user.password_hash)
    else:
        # Burn constant time even if user doesn't exist
        verify_password(req.password, "$2b$12$invalid.hash")
    
    # Return 401 if either check failed (generic message to prevent enumeration)
    if not user or not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Set signed session cookie
    request.session["user_id"] = user.id
    
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user.
    
    **Contract:**
    - Requires valid signed session cookie
    - Returns User {id, email, created_at}
    - Raises 401 if cookie missing/invalid/expired
    
    Uses get_current_user dependency which:
    - Extracts user_id from session
    - Looks up User from database
    - Raises 401 if any step fails
    
    This is the client's bootstrap endpoint to validate session on page load.
    """
    return UserResponse.model_validate(current_user)
