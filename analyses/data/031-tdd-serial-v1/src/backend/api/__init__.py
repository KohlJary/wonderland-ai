"""API routers — aggregated and mounted by main.py."""

from fastapi import APIRouter

from src.backend.api.health import router as health_router
from src.backend.api.sessions import router as sessions_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(sessions_router, prefix="/api")
