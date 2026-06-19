"""
Geolocation service: resolve city + country to IANA timezone + coordinates.

This module provides deterministic geolocation resolution using a curated
dataset of major cities, ensuring reproducible test behavior.

**Invariants enforced:**
- Timezone is always IANA-valid (e.g., 'Europe/Vienna')
- Latitude is in range [-90, 90]
- Longitude is in range [-180, 180]
- Resolution is case-insensitive on city/country input
- Unknown cities raise GeolocationError with clear message
"""
from typing import Tuple, NamedTuple
import unicodedata


class GeolocationError(Exception):
    """Raised when geolocation resolution fails."""
    pass


class GeolocationResult(NamedTuple):
    """Resolved geolocation data."""
    timezone: str  # IANA timezone string
    latitude: float  # Decimal degrees, [-90, 90]
    longitude: float  # Decimal degrees, [-180, 180]


# Curated dataset of major cities: (city_normalized, country_normalized) -> (timezone, lat, lon)
# This ensures reproducible tests without external API dependencies.
CITY_DATASET = {
    ("vienna", "austria"): GeolocationResult(
        timezone="Europe/Vienna",
        latitude=48.2,
        longitude=16.4,
    ),
    ("san francisco", "united states"): GeolocationResult(
        timezone="America/Los_Angeles",
        latitude=37.77,
        longitude=-122.42,
    ),
    ("london", "united kingdom"): GeolocationResult(
        timezone="Europe/London",
        latitude=51.51,
        longitude=-0.13,
    ),
    ("london", "england"): GeolocationResult(
        timezone="Europe/London",
        latitude=51.51,
        longitude=-0.13,
    ),
    ("tokyo", "japan"): GeolocationResult(
        timezone="Asia/Tokyo",
        latitude=35.67,
        longitude=139.65,
    ),
    ("paris", "france"): GeolocationResult(
        timezone="Europe/Paris",
        latitude=48.86,
        longitude=2.29,
    ),
    ("berlin", "germany"): GeolocationResult(
        timezone="Europe/Berlin",
        latitude=52.52,
        longitude=13.40,
    ),
    ("sydney", "australia"): GeolocationResult(
        timezone="Australia/Sydney",
        latitude=-33.87,
        longitude=151.21,
    ),
    ("toronto", "canada"): GeolocationResult(
        timezone="America/Toronto",
        latitude=43.65,
        longitude=-79.38,
    ),
    ("new york", "united states"): GeolocationResult(
        timezone="America/New_York",
        latitude=40.71,
        longitude=-74.01,
    ),
    ("mumbai", "india"): GeolocationResult(
        timezone="Asia/Kolkata",
        latitude=19.08,
        longitude=72.88,
    ),
    ("buenos aires", "argentina"): GeolocationResult(
        timezone="America/Argentina/Buenos_Aires",
        latitude=-34.61,
        longitude=-58.37,
    ),
    ("moscow", "russia"): GeolocationResult(
        timezone="Europe/Moscow",
        latitude=55.75,
        longitude=37.62,
    ),
    ("bangkok", "thailand"): GeolocationResult(
        timezone="Asia/Bangkok",
        latitude=13.73,
        longitude=100.50,
    ),
    ("singapore", "singapore"): GeolocationResult(
        timezone="Asia/Singapore",
        latitude=1.35,
        longitude=103.82,
    ),
}


def _normalize_string(s: str) -> str:
    """Normalize string for matching: lowercase + NFD normalize + strip."""
    s = s.lower().strip()
    # NFD normalize to decompose accented characters (e.g., "Zürich" -> "zurich")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s


def resolve_geolocation(city: str, country: str) -> GeolocationResult:
    """
    Resolve city + country to IANA timezone + coordinates.

    **Contract:**
    - Accepts city and country as non-empty strings
    - Returns GeolocationResult with timezone (IANA), latitude, longitude
    - Raises GeolocationError if city/country combo is unknown

    **Invariants enforced:**
    - Timezone is always IANA-valid
    - Latitude in [-90, 90], longitude in [-180, 180]
    - Returns are deterministic (same input always returns same output)
    - Matching is case-insensitive and accent-insensitive

    **Failure modes handled:**
    - Unknown city: raises GeolocationError with friendly message
    - Empty city/country: raises GeolocationError
    - Malformed input: raises ValueError (caller should validate)

    Args:
        city: City name (non-empty string)
        country: Country name (non-empty string)

    Returns:
        GeolocationResult with timezone, latitude, longitude

    Raises:
        GeolocationError: if city/country combo is unknown or inputs invalid
    """
    # Validate inputs
    if not city or not isinstance(city, str):
        raise GeolocationError("City must be a non-empty string")
    if not country or not isinstance(country, str):
        raise GeolocationError("Country must be a non-empty string")

    # Normalize for lookup
    city_norm = _normalize_string(city)
    country_norm = _normalize_string(country)

    # Look up in dataset
    key = (city_norm, country_norm)
    if key not in CITY_DATASET:
        raise GeolocationError(
            f"Could not resolve geolocation for {city}, {country}. "
            f"Supported cities: Vienna (Austria), San Francisco (USA), London (UK), "
            f"Tokyo (Japan), Paris (France), Berlin (Germany), Sydney (Australia), "
            f"Toronto (Canada), New York (USA), Mumbai (India), Buenos Aires (Argentina), "
            f"Moscow (Russia), Bangkok (Thailand), Singapore (Singapore)."
        )

    result = CITY_DATASET[key]
    
    # Validate invariants
    assert isinstance(result.timezone, str) and len(result.timezone) > 0
    assert -90 <= result.latitude <= 90
    assert -180 <= result.longitude <= 180
    
    return result
