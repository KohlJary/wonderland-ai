"""API routers — aggregated and mounted by main.py."""

from fastapi import APIRouter

from src.backend.api.health import router as health_router
from src.backend.api.sessions import router as sessions_router
from src.backend.api.breaks import router as breaks_router
from src.backend.api.settings import router as settings_router
from src.backend.api.history import router as history_router
from src.backend.api.statistics import router as statistics_router
from src.backend.api.user import router as user_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(sessions_router)
api_router.include_router(breaks_router)
api_router.include_router(settings_router)
api_router.include_router(history_router)
api_router.include_router(statistics_router)
api_router.include_router(user_router)
