"""API routers — aggregated and mounted by main.py.

Routers:
- health: /api/health (status checks)
- notes: /api/notes* (POST create, GET list, GET/{id} read, PUT/{id} update, DELETE/{id} delete)
         /api/notes/{id}/tags* (POST associate, DELETE/{tag_id} remove)
"""

from fastapi import APIRouter

from src.backend.api.health import router as health_router
from src.backend.api.notes import router as notes_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(notes_router, prefix="/api")
