"""FastAPI app entrypoint.

Wires the SQLAlchemy engine, creates tables on startup (SQLite +
create_all is fine for development; production deployment would add
Alembic migrations), mounts the API router, configures permissive
CORS for the local frontend dev server.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.api import api_router
from src.backend.db import engine
from src.backend.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="fullstack-app", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
