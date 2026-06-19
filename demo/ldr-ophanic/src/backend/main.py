"""
FastAPI application entry point.
Sets up database, session middleware, auth endpoints, protected routes, and scheduled polling jobs.
"""
import os
import secrets
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.backend.database import Base
from src.backend.routers import auth_router, partner_router, dashboard_router, api_router
from src.backend.polling_job import poll_weather_hourly, poll_austrian_news_daily, init_db_engine

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Session secret from environment
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY:
    raise RuntimeError(
        "SESSION_SECRET_KEY environment variable is required. "
        "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
    )


# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite+aiosqlite:///./app.db"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    """Dependency: get database session."""
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context: create tables on startup, set up scheduler, close engine on shutdown.
    
    **Startup flow:**
    1. Create database tables (idempotent via SQLAlchemy)
    2. Initialize database engine for polling job
    3. Set up APScheduler for hourly weather polling
    4. Start the scheduler
    
    **Shutdown flow:**
    1. Shut down the scheduler gracefully
    2. Close the database engine
    """
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize database engine for polling job
    init_db_engine()
    
    # Set up and start scheduler for hourly polling
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        poll_weather_hourly,
        "interval",
        hours=1,
        id="poll_weather_hourly",
        name="Hourly weather polling from Open-Meteo",
    )
    scheduler.add_job(
        poll_austrian_news_daily,
        "cron",
        hour=0,
        minute=0,
        id="poll_austrian_news_daily",
        name="Daily Austrian news polling from Der Standard + ORF RSS feeds",
    )
    scheduler.start()
    logger.info("Hourly weather polling job scheduled (runs every 1 hour)")
    logger.info("Daily news polling job scheduled (runs daily at 00:00 UTC)")
    
    yield
    
    # Shutdown: stop scheduler and close engine
    scheduler.shutdown(wait=True)
    logger.info("Weather polling scheduler shut down")
    await engine.dispose()


# FastAPI app
app = FastAPI(
    title="LDR Ophanic",
    description="Long-distance relationship dashboard",
    version="0.1.0",
    lifespan=lifespan,
)

# Session middleware (signed cookies, httpOnly, sameSite strict)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    session_cookie="session",
    max_age=7 * 24 * 60 * 60,  # 7 days in seconds
    same_site="strict",
    https_only=os.getenv("ENVIRONMENT", "development") == "production",
)

# Auth routes (signup, signin, /auth/me)
app.include_router(auth_router.router)

# Partner routes (set and retrieve partner profile)
app.include_router(partner_router.router)

# API routes (GET /api/dashboard returns partner profile + cached weather/news)
app.include_router(api_router.router)

# Dashboard route (serve React SPA entry point to authenticated users)
app.include_router(dashboard_router.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
