"""
Partner profile endpoints: set (POST /partner) and retrieve (GET /partner).

These endpoints are authenticated and partner-profile operations on the User's own profile.
There is a 1:1 relationship between User and PartnerProfile; POST /partner replaces
the previous profile (single snapshot, no history).
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.database import User, PartnerProfile
from src.backend.dependencies import get_current_user, get_db
from src.backend.geolocation import resolve_geolocation, GeolocationError

router = APIRouter(prefix="/partner", tags=["partner"])


# Request/response schemas
class PartnerProfileRequest(BaseModel):
    """POST /partner request."""
    name: str
    city: str
    country: str

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Sarah",
                "city": "Vienna",
                "country": "Austria",
            }
        }


class PartnerProfileResponse(BaseModel):
    """Partner profile response."""
    id: int
    name: str
    city: str
    country: str
    timezone: str
    latitude: float
    longitude: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Error response."""
    error: str


# Endpoints

@router.post("", response_model=PartnerProfileResponse, status_code=201)
async def set_partner_profile(
    req: PartnerProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Set or update user's partner profile.

    **Contract:**
    - Requires authenticated session (user_id from cookie)
    - Accepts POST /partner { name, city, country }
    - Validates all three fields are non-empty strings
    - Calls geolocation resolver to resolve city/country → timezone + coordinates
    - Stores/updates PartnerProfile record (one per user, replaces previous)
    - Returns 201 + resolved profile { id, name, city, country, timezone, latitude, longitude, created_at, updated_at }

    **Invariants enforced:**
    - Each User has at most one PartnerProfile (UNIQUE(user_id) constraint)
    - Partner location is never logged or exposed in error messages (PII handling)
    - Timezone is IANA-valid
    - Coordinates are plausible (lat in [-90, 90], lon in [-180, 180])
    - created_at is immutable; updated_at reflects the latest write

    **Failure modes handled:**
    - Missing/empty fields: HTTPException(400 Bad Request)
    - Geolocation failure (unknown city): HTTPException(400 Bad Request) with friendly message
    - Database error: exception propagates (will result in 500)

    Args:
        req: PartnerProfileRequest with name, city, country
        current_user: authenticated User from session
        db: database session

    Returns:
        PartnerProfileResponse with resolved profile data
    """
    # Validate inputs
    if not req.name or not req.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Partner name is required",
        )
    if not req.city or not req.city.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="City is required",
        )
    if not req.country or not req.country.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Country is required",
        )

    # Resolve geolocation
    try:
        geo_result = resolve_geolocation(req.city, req.country)
    except GeolocationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Check if user already has a partner profile
    result = await db.execute(
        select(PartnerProfile).where(PartnerProfile.user_id == current_user.id)
    )
    existing_profile = result.scalar_one_or_none()

    # Create or update profile
    if existing_profile:
        # Replace the profile (single snapshot semantics)
        existing_profile.name = req.name.strip()
        existing_profile.city = req.city.strip()
        existing_profile.country = req.country.strip()
        existing_profile.timezone = geo_result.timezone
        existing_profile.latitude = str(geo_result.latitude)
        existing_profile.longitude = str(geo_result.longitude)
        existing_profile.updated_at = datetime.utcnow()
        partner_profile = existing_profile
    else:
        # Create new profile
        partner_profile = PartnerProfile(
            user_id=current_user.id,
            name=req.name.strip(),
            city=req.city.strip(),
            country=req.country.strip(),
            timezone=geo_result.timezone,
            latitude=str(geo_result.latitude),
            longitude=str(geo_result.longitude),
        )
        db.add(partner_profile)

    # Commit and return
    await db.commit()
    await db.refresh(partner_profile)

    return PartnerProfileResponse.model_validate(partner_profile)


@router.get("", response_model=PartnerProfileResponse)
async def get_partner_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's partner profile.

    **Contract:**
    - Requires authenticated session (user_id from cookie)
    - Returns 200 + partner profile if set, or 404 if not yet set

    **Invariants enforced:**
    - Returns only the current user's own partner profile (no cross-user access)
    - Timezone and coordinates are always present (validated at set time)

    **Failure modes handled:**
    - No partner profile set: HTTPException(404 Not Found)
    - Database error: exception propagates (will result in 500)

    Args:
        current_user: authenticated User from session
        db: database session

    Returns:
        PartnerProfileResponse with resolved profile data

    Raises:
        HTTPException(404): if partner profile not yet set
    """
    # Query for this user's partner profile
    result = await db.execute(
        select(PartnerProfile).where(PartnerProfile.user_id == current_user.id)
    )
    partner_profile = result.scalar_one_or_none()

    if partner_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner profile not set",
        )

    return PartnerProfileResponse.model_validate(partner_profile)
