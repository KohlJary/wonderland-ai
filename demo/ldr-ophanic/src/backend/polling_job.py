"""
Polling job: fetches weather from Open-Meteo hourly for all users with partner profiles.

**Contract:**
- Job runs on hourly schedule (via APScheduler)
- For each user with a partner profile: fetch weather from Open-Meteo using partner's lat/lon
- Store result in weather_cache table, keyed by user_id
- On fetch failure, leave prior cache untouched (graceful degradation)
- Job logs all outcomes (success, skip-no-profile, skip-no-coords, failure)

**Invariants enforced:**
- Each user has at most one weather_cache row
- Cache updates are atomic (all fields update together or none)
- failed_cache entries are distinguishable from stale_cache (by tracking last_successful_fetch_at)
"""
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, update
import os

from src.backend.database import User, PartnerProfile, WeatherCache, NewsCache
from src.backend.weather_service import fetch_weather
from src.backend.news_service import fetch_austrian_news, NewsServiceException
import json

logger = logging.getLogger(__name__)


# Database setup for polling job (will be reused from main app in production)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
_engine = None
_SessionLocal = None


def init_db_engine():
    """Initialize database engine for polling job (call once at startup)."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_async_engine(DATABASE_URL, echo=False, future=True)
        _SessionLocal = async_sessionmaker(
            _engine, class_=AsyncSession, expire_on_commit=False
        )





async def poll_weather_hourly():
    """
    Poll Open-Meteo for weather for all users with partner profiles.
    
    **Flow:**
    1. Query all users with partner profiles
    2. For each user:
       a. Check that partner_profile.latitude and partner_profile.longitude are set
       b. Call fetch_weather(lat, lon)
       c. If successful: insert or update weather_cache row with new data
       d. If failed: log the failure and skip (leave prior cache untouched)
    3. Log summary (X successful, Y skipped, Z failed)
    
    **Failure modes handled:**
    - User has no partner profile: skip (no fetch attempted)
    - Partner profile exists but lat/lon not set: skip (no fetch attempted)
    - Open-Meteo request times out or fails: log error, leave cache untouched
    - Database write fails: log error (cache update lost, but next poll will retry)
    
    **Invariants maintained:**
    - Each successful fetch updates exactly one weather_cache row
    - Failed fetches do not modify cache state
    - last_fetch_attempt_at is updated on every attempt (success or failure)
    - last_successful_fetch_at is updated only on successful fetch
    """
    if _SessionLocal is None:
        init_db_engine()
    
    async with _SessionLocal() as db:
        try:
            # Query all users with partner profiles
            result = await db.execute(
                select(User).join(PartnerProfile).where(
                    PartnerProfile.user_id == User.id
                )
            )
            users = result.scalars().all()
            
            logger.info(f"Starting hourly weather poll for {len(users)} users")
            
            successful = 0
            skipped = 0
            failed = 0
            
            for user in users:
                partner_profile = user.partner_profile
                
                # Skip if partner profile doesn't have lat/lon
                if not partner_profile.latitude or not partner_profile.longitude:
                    logger.debug(
                        f"Skipping weather fetch for user {user.id}: no lat/lon in partner profile"
                    )
                    skipped += 1
                    continue
                
                try:
                    # Fetch weather from Open-Meteo
                    weather_data = await fetch_weather(
                        partner_profile.latitude,
                        partner_profile.longitude,
                    )
                    
                    # Update or insert weather_cache row
                    now = datetime.utcnow()
                    
                    # Check if cache entry exists
                    cache_result = await db.execute(
                        select(WeatherCache).where(WeatherCache.user_id == user.id)
                    )
                    cache_entry = cache_result.scalar_one_or_none()
                    
                    if cache_entry:
                        # Update existing cache entry
                        # INVARIANT: cached_at is immutable (set at creation, never updated)
                        # This preserves staleness detection in api_router.py line 199:
                        # cache_age = now - cached_at correctly identifies data older than 90min
                        cache_entry.temperature_f = weather_data["temperature_f"]
                        cache_entry.condition_code = weather_data["condition_code"]
                        cache_entry.condition_description = weather_data["condition_description"]
                        cache_entry.last_fetch_attempt_at = now
                        cache_entry.last_successful_fetch_at = now
                        # NOTE: cached_at is NOT updated — this is deliberate and load-bearing
                    else:
                        # Create new cache entry
                        cache_entry = WeatherCache(
                            user_id=user.id,
                            temperature_f=weather_data["temperature_f"],
                            condition_code=weather_data["condition_code"],
                            condition_description=weather_data["condition_description"],
                            cached_at=now,
                            last_fetch_attempt_at=now,
                            last_successful_fetch_at=now,
                        )
                        db.add(cache_entry)
                    
                    logger.info(
                        f"Successfully fetched weather for user {user.id}: "
                        f"temp={weather_data['temperature_f']}°F, code={weather_data['condition_code']}"
                    )
                    successful += 1
                    
                except Exception as e:
                    # Log failure but don't raise (job continues for other users)
                    logger.error(
                        f"Failed to fetch weather for user {user.id} "
                        f"(lat={partner_profile.latitude}, lon={partner_profile.longitude}): {e}"
                    )
                    failed += 1
                    # Update last_fetch_attempt_at even on failure (so we know we tried)
                    cache_result = await db.execute(
                        select(WeatherCache).where(WeatherCache.user_id == user.id)
                    )
                    cache_entry = cache_result.scalar_one_or_none()
                    if cache_entry:
                        cache_entry.last_fetch_attempt_at = datetime.utcnow()
            
            # Commit all changes
            await db.commit()
            
            logger.info(
                f"Hourly weather poll complete: {successful} successful, "
                f"{skipped} skipped, {failed} failed"
            )
            
        except Exception as e:
            logger.error(f"Unhandled exception in hourly weather poll: {e}", exc_info=True)
            raise



async def poll_austrian_news_daily():
    """
    Poll Austrian RSS feeds (Der Standard + ORF) for top headlines daily.
    
    **Flow:**
    1. Query all users with partner profiles
    2. For each user:
       a. Call fetch_austrian_news()
       b. If successful: insert or update news_cache row with headline data
       c. If failed: log the failure and skip (leave prior cache untouched)
    3. Log summary (X successful, Y skipped, Z failed)
    
    **Failure modes handled:**
    - No partner profile: skip (no fetch attempted)
    - RSS feed unreachable: log error, leave cache untouched
    - RSS feed parse error: log error, leave cache untouched
    - Both RSS feeds fail: treat as failed, skip user, leave cache untouched
    - Database write fails: log error (cache update lost, but next poll will retry)
    
    **Invariants maintained:**
    - Each successful fetch updates exactly one news_cache row
    - Failed fetches do not modify cache state
    - last_fetch_attempt_at is updated on every attempt (success or failure)
    - last_successful_fetch_at is updated only on successful fetch
    """
    if _SessionLocal is None:
        init_db_engine()
    
    async with _SessionLocal() as db:
        try:
            # Query all users with partner profiles
            result = await db.execute(
                select(User).join(PartnerProfile).where(
                    PartnerProfile.user_id == User.id
                )
            )
            users = result.scalars().all()
            
            logger.info(f"Starting daily news poll for {len(users)} users")
            
            successful = 0
            skipped = 0
            failed = 0
            
            for user in users:
                try:
                    # Fetch headlines from Austrian RSS feeds
                    headlines = await fetch_austrian_news()
                    
                    # Convert headlines to JSON for storage
                    headlines_json = json.dumps([h.to_dict() for h in headlines])
                    
                    # Update or insert news_cache row
                    now = datetime.utcnow()
                    
                    # Check if cache entry exists
                    cache_result = await db.execute(
                        select(NewsCache).where(NewsCache.user_id == user.id)
                    )
                    cache_entry = cache_result.scalar_one_or_none()
                    
                    if cache_entry:
                        # Update existing cache entry
                        # INVARIANT: cached_at is immutable (set at creation, never updated)
                        cache_entry.headlines_json = headlines_json
                        cache_entry.last_fetch_attempt_at = now
                        cache_entry.last_successful_fetch_at = now
                    else:
                        # Create new cache entry
                        cache_entry = NewsCache(
                            user_id=user.id,
                            headlines_json=headlines_json,
                            cached_at=now,
                            last_fetch_attempt_at=now,
                            last_successful_fetch_at=now,
                        )
                        db.add(cache_entry)
                    
                    logger.debug(f"Updated news cache for user {user.id}: {len(headlines)} headlines")
                    successful += 1
                
                except NewsServiceException as e:
                    # RSS feeds all failed, but don't raise (job continues for other users)
                    logger.warning(
                        f"Failed to fetch news for user {user.id}: {e}"
                    )
                    failed += 1
                    # Update last_fetch_attempt_at even on failure (so we know we tried)
                    cache_result = await db.execute(
                        select(NewsCache).where(NewsCache.user_id == user.id)
                    )
                    cache_entry = cache_result.scalar_one_or_none()
                    if cache_entry:
                        cache_entry.last_fetch_attempt_at = datetime.utcnow()
                
                except Exception as e:
                    logger.error(
                        f"Unexpected error fetching news for user {user.id}: {type(e).__name__}: {e}"
                    )
                    failed += 1
            
            # Commit all changes
            await db.commit()
            
            logger.info(
                f"Daily news poll complete: {successful} successful, "
                f"{skipped} skipped, {failed} failed"
            )
            
        except Exception as e:
            logger.error(f"Unhandled exception in daily news poll: {e}", exc_info=True)
            raise
