"""FastAPI app — extend with new routes.

Add routes by registering them on ``app`` (or by attaching an
``APIRouter`` and including it). Group related routes into
modules under ``src/`` (e.g., ``src/users.py``,
``src/items.py``) and import their routers here.
"""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="App", version="0.0.1")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe. Returns 200 with a status payload."""
    return {"status": "ok"}
