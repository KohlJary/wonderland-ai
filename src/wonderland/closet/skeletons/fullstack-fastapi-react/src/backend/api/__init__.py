"""API routers — aggregated and mounted by main.py.

============================================================================
SKELETON TEMPLATE — the messages_router lines below are placeholder.

When you delete src/backend/api/messages.py (the placeholder
endpoint file), you MUST also delete the two `messages_router`
lines below. Otherwise this module fails to import and the whole
backend (including conftest.py and all tests) breaks at collection
time.

The health_router lines stay regardless — /api/health is a real
endpoint the team should preserve.
============================================================================
"""

from fastapi import APIRouter

from src.backend.api.health import router as health_router

# === TEMPLATE: delete the next line when removing messages.py ===
from src.backend.api.messages import router as messages_router

api_router = APIRouter()
api_router.include_router(health_router)
# === TEMPLATE: delete the next line when removing messages.py ===
api_router.include_router(messages_router, prefix="/api")
