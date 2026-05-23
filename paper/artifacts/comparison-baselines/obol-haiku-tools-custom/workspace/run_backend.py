#!/usr/bin/env python3
"""Run the Finance backend server."""
import sys

from src.backend.main import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
