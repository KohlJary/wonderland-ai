"""
FastAPI dependencies for session management and authentication.

Core: GetCurrentUser dependency extracts user_id from signed session cookie,
looks up User from database, returns User or raises 401.
"""
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.database import User


async def get_db(request: Request) -> AsyncSession:
    """
    Dependency: get database session from request.
    
    The FastAPI lifespan ensures AsyncSessionLocal is available on app.state.
    """
    # This will be injected by the lifespan context
    from src.backend.main import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        return session


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency: extract user_id from signed session cookie, resolve to User or 401.
    
    **Contract:**
    - Reads 'session' cookie from request (FastAPI's SessionMiddleware signed it)
    - Extracts 'user_id' from session dict
    - Queries User table for matching id
    - Returns User object if found and valid
    - Raises HTTPException(401) if cookie missing, invalid, expired, or user not found
    
    **Invariants enforced:**
    - user_id in session is an integer and non-negative
    - User with that id exists in database
    - No user object is returned if either condition fails
    
    **Failure modes handled:**
    - Missing cookie: HTTPException(401 Unauthorized)
    - Missing/malformed user_id in session: HTTPException(401 Unauthorized)
    - User id not in database: HTTPException(401 Unauthorized)
    - Database query failure: exception propagates (will result in 500)
    """
    # Extract session dict from request
    session = request.session
    
    # Extract user_id from session
    user_id = session.get("user_id")
    
    # Validate user_id is present and valid type
    if user_id is None or not isinstance(user_id, int) or user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Query database for user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    # Return user or 401
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user
