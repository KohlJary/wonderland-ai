"""
Dashboard page endpoint: GET /dashboard serves the React SPA entry point.

**Contract:**
- GET /dashboard with valid session → 200 + index.html (SPA entry point)
- GET /dashboard without session → 401 Unauthorized (frontend ProtectedRoute redirects to /sign-in)
- React app loads on the client and mounts; hydration bootstrap calls GET /auth/me 
  to validate session and GET /api/dashboard to load partner + cached data

**Invariants enforced:**
- Only authenticated users can access /dashboard (session validation)
- index.html is always served (no 404 for authenticated users)
- Unauthenticated requests receive 401 (client-side routing handles redirect)

**Failure modes handled:**
- No session: 401 Unauthorized (client-side ProtectedRoute redirects)
- Invalid/expired session: 401 Unauthorized (client-side ProtectedRoute redirects)
- Frontend serves index.html for all authenticated paths (SPA routing handled client-side)
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.database import User
from src.backend.dependencies import get_current_user, get_db

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
async def dashboard(
    current_user: User = Depends(get_current_user),
):
    """
    Serve the React SPA entry point (index.html) for authenticated users.
    
    **Flow:**
    1. Request comes in with session cookie
    2. get_current_user validates session and returns User (or 401)
    3. If User is present, serve index.html
    4. React hydrates on client, mounts App, AuthProvider validates session via GET /auth/me
    5. If authenticated, App routes to /dashboard and renders Dashboard component
    6. Dashboard component fetches GET /api/dashboard to load partner profile + cached weather/news
    
    **Args:**
    current_user: authenticated User from session (get_current_user raises 401 if invalid)
    
    **Returns:**
    FileResponse: index.html with 200 status
    
    **Unauthenticated flow:**
    - If no session or invalid session, get_current_user raises HTTPException(401)
    - The frontend's ProtectedRoute component handles this: if GET /auth/me returns 
      401, ProtectedRoute redirects to /sign-in
    - So this endpoint truly returns 401 to the browser, and the browser's JS handles
      the redirect (not server-side redirect here)
    """
    # Compute absolute path to index.html relative to this module.
    # This file is at src/backend/routers/dashboard_router.py;
    # index.html is at the project root, so we go up three directory levels.
    index_html_path = os.path.join(os.path.dirname(__file__), "../../../index.html")
    return FileResponse(path=index_html_path, media_type="text/html")
