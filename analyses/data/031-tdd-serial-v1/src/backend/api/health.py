"""GET /health — liveness check. Returns 200 with a small JSON
status body. Common pattern for load balancers + monitoring."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
