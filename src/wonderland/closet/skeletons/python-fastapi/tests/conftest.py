"""Pytest fixtures for FastAPI tests.

``client`` returns a ``TestClient`` wrapping the app — sync, no
event loop needed for basic route testing. For async test cases
(database, real httpx calls), pull in ``httpx.AsyncClient`` +
pytest-asyncio.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
