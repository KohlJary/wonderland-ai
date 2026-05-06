"""API routers — aggregated and mounted by main.py."""

from fastapi import APIRouter

from src.backend.api.health import router as health_router
from src.backend.api.messages import router as messages_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(messages_router, prefix="/api")
