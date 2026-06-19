"""Routers package."""
from .auth_router import router as auth_router
from .partner_router import router as partner_router
from .dashboard_router import router as dashboard_router
from .api_router import router as api_router

__all__ = ["auth_router", "partner_router", "dashboard_router", "api_router"]
