"""
API endpoints for dashboard data: GET /api/dashboard returns partner profile + cached weather/news.

**Contract (contract-note-01KV9PRX):**
- GET /api/dashboard (NO URL param; partner_id derived from authenticated session)
- Requires authentication (401 if unauthenticated)
- Returns single response object:
  {
    partner_timezone: string (IANA timezone),
    weather: {
      current_conditions: string | null,
      temp_f: number | null,
      is_stale: bool,
      last_updated_at: ISO8601 | null,
      error: string | null
    },
    news: {
      headlines: [{title: string, excerpt: string, source: string, url: string}] | null,
      is_stale: bool,
      last_updated_at: ISO8601 | null,
      error: string | null
    }
  }
- error field carries stable machine keys: 'not_yet_available', 'unavailable', 'degraded'
- is_stale: true when cache age > 90min for weather, > 24h for news
- Background polling (separate tickets) populates cache asynchronously
- GET /api/dashboard never blocks on external APIs

**Invariants enforced:**
- Only authenticated users can access this endpoint
- partner_timezone is always a non-empty IANA string if partner profile exists
- weather and news objects have consistent shape regardless of cache state
- error field is mutually exclusive with data (if error is not null, data is null)

**Failure modes handled:**
- No authentication: 401 Unauthorized
- User has no partner profile: 404 Not Found
- Cache never populated: error='not_yet_available', data=null
- Cache stale: is_stale=true, returns cached data with staleness indication
"""
from datetime import datetime, timedelta
from typing import Optional, List
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.database import User, PartnerProfile, WeatherCache, NewsCache
from src.backend.dependencies import get_current_user, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])


# Response schemas
class HeadlineResponse(BaseModel):
    """Single news headline."""
    title: str
    excerpt: str
    source: str
    url: str


class WeatherResponse(BaseModel):
    """Weather card data."""
    current_conditions: Optional[str] = None
    temp_f: Optional[float] = None
    is_stale: bool
    last_updated_at: Optional[str] = None  # ISO8601 string
    error: Optional[str] = None  # 'not_yet_available' | 'unavailable' | 'degraded'


class NewsResponse(BaseModel):
    """News card data."""
    headlines: Optional[List[HeadlineResponse]] = None
    is_stale: bool
    last_updated_at: Optional[str] = None  # ISO8601 string
    error: Optional[str] = None  # 'not_yet_available' | 'unavailable' | 'degraded'


class DashboardResponse(BaseModel):
    """Complete dashboard response."""
    partner_timezone: str
    weather: WeatherResponse
    news: NewsResponse

    class Config:
        from_attributes = True


# Endpoints

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get authenticated user's dashboard data: partner profile + cached weather/news.

    **Contract:**
    - Requires valid session (current_user dependency enforces authentication)
    - Returns partner timezone + weather/news cache placeholders
    - Never blocks on external APIs (cache is populated asynchronously by separate service)

    **Flow:**
    1. get_current_user validates session and returns User (or raises 401)
    2. Query PartnerProfile for current_user.id
    3. If no profile exists, return 404 Not Found
    4. If profile exists, extract timezone
    5. Query weather cache table and assess staleness
    6. Return complete dashboard response with cache state indicators

    **Args:**
    current_user: authenticated User from session (get_current_user raises 401 if invalid)
    db: database session

    **Returns:**
    DashboardResponse with partner timezone + weather/news cache state

    **Raises:**
    HTTPException(404): user has no partner profile
    HTTPException(401): invalid/missing session (raised by get_current_user)
    
    **Staleness rules:**
    - Weather is stale if cache_age > 90 minutes
    - News is stale if cache_age > 24 hours (news polling not yet implemented, always returns not_yet_available)
    """
    # Query partner profile for current user
    result = await db.execute(
        select(PartnerProfile).where(PartnerProfile.user_id == current_user.id)
    )
    partner_profile = result.scalar_one_or_none()

    # If no partner profile, return 404
    if partner_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner profile not found. Please set up your partner profile first.",
        )

    # Query weather cache for current user
    weather_result = await db.execute(
        select(WeatherCache).where(WeatherCache.user_id == current_user.id)
    )
    weather_cache = weather_result.scalar_one_or_none()

    # Query news cache for current user
    news_result = await db.execute(
        select(NewsCache).where(NewsCache.user_id == current_user.id)
    )
    news_cache = news_result.scalar_one_or_none()

    # Build weather response based on cache state
    now = datetime.utcnow()
    weather_response = _build_weather_response(weather_cache, now)

    # Build news response based on cache state
    news_response = _build_news_response(news_cache, now)

    return DashboardResponse(
        partner_timezone=partner_profile.timezone,
        weather=weather_response,
        news=news_response,
    )


def _build_weather_response(weather_cache: Optional[WeatherCache], now: datetime) -> WeatherResponse:
    """
    Build WeatherResponse from cache state.
    
    **Logic:**
    - No cache: error='not_yet_available', is_stale=False, data=null
    - Cache exists, fresh (< 90 min): return cached data, is_stale=False, error=None
    - Cache exists, stale (>= 90 min): return cached data, is_stale=True, error='degraded'
    - Cache row exists but last_successful_fetch_at is null: never successfully fetched, error='unavailable', is_stale=False, data=null
    
    **Args:**
    weather_cache: WeatherCache row or None
    now: current datetime (UTC)
    
    **Returns:**
    WeatherResponse with consistent shape regardless of cache state
    """
    if weather_cache is None:
        # No cache ever populated
        return WeatherResponse(
            is_stale=False,
            error="not_yet_available",
        )
    
    # Check if cache has ever been successfully populated
    if weather_cache.last_successful_fetch_at is None:
        # Cache entry exists but never succeeded (no usable data to show)
        # Per scenario-01KVC8NR: unavailable means no data, not stale data
        return WeatherResponse(
            is_stale=False,
            error="unavailable",
        )
    
    # Calculate cache age
    cache_age = now - weather_cache.cached_at
    staleness_threshold = timedelta(minutes=90)
    is_stale = cache_age >= staleness_threshold
    
    # Return cached data with staleness indicator
    error = "degraded" if is_stale else None
    
    return WeatherResponse(
        current_conditions=weather_cache.condition_description,
        temp_f=weather_cache.temperature_f,
        is_stale=is_stale,
        last_updated_at=weather_cache.cached_at.isoformat() if weather_cache.cached_at else None,
        error=error,
    )


def _build_news_response(news_cache: Optional[NewsCache], now: datetime) -> NewsResponse:
    """
    Build NewsResponse from cache state.
    
    **Logic:**
    - No cache: error='not_yet_available', is_stale=False, data=null
    - Cache exists, fresh (< 24 hours): return cached data, is_stale=False, error=None
    - Cache exists, stale (>= 24 hours): return cached data, is_stale=True, error='degraded'
    - Cache row exists but last_successful_fetch_at is null: never successfully fetched, 
      error='unavailable', is_stale=False, data=null
    
    **Args:**
    news_cache: NewsCache row or None
    now: current datetime (UTC)
    
    **Returns:**
    NewsResponse with consistent shape regardless of cache state
    """
    if news_cache is None:
        # No cache ever populated
        return NewsResponse(
            is_stale=False,
            error="not_yet_available",
        )
    
    # Check if cache has ever been successfully populated
    if news_cache.last_successful_fetch_at is None:
        # Cache entry exists but never succeeded (no usable data to show)
        return NewsResponse(
            is_stale=False,
            error="unavailable",
        )
    
    # Calculate cache age
    cache_age = now - news_cache.cached_at
    staleness_threshold = timedelta(hours=24)
    is_stale = cache_age >= staleness_threshold
    
    # Parse headlines from JSON
    headlines = []
    try:
        if news_cache.headlines_json:
            headlines_data = json.loads(news_cache.headlines_json)
            headlines = [
                HeadlineResponse(
                    title=h.get("title", ""),
                    excerpt=h.get("title", ""),  # Use title as excerpt for RSS
                    source=h.get("source", ""),
                    url=h.get("url", ""),
                )
                for h in headlines_data
            ]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(f"Failed to parse cached news JSON: {e}")
        return NewsResponse(
            is_stale=is_stale,
            error="degraded",
            last_updated_at=news_cache.cached_at.isoformat() if news_cache.cached_at else None,
        )
    
    # Return cached data with staleness indicator
    error = "degraded" if is_stale else None
    
    return NewsResponse(
        headlines=headlines if headlines else None,
        is_stale=is_stale,
        last_updated_at=news_cache.cached_at.isoformat() if news_cache.cached_at else None,
        error=error,
    )
