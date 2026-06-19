"""
Weather service: fetches from Open-Meteo API and manages cache.

**Contract:**
- fetch_weather(latitude, longitude) returns {temp_f, condition_code, condition_description}
  or raises an exception on failure (which the polling job catches)
- Polling job runs hourly, fetches for all users with partner profiles set
- Cache persists in SQLite weather_cache table, keyed by user_id
- On fetch failure, prior cache is left untouched (graceful degradation)

**Invariants enforced:**
- Temperature is always in Fahrenheit (converted from Open-Meteo's Celsius)
- WMO weather code is preserved as-is from Open-Meteo
- Condition description is human-readable English
- Each user has at most one weather_cache row (unique constraint on user_id)
"""
import httpx
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Open-Meteo API endpoint (free, no key required)
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather code to human-readable description mapping
# See: https://www.open-meteo.com/en/docs
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


async def fetch_weather(latitude: str, longitude: str) -> Dict[str, Any]:
    """
    Fetch current weather from Open-Meteo API.
    
    Args:
        latitude: decimal latitude as string (e.g., "48.2")
        longitude: decimal longitude as string (e.g., "16.4")
    
    Returns:
        {
            "temperature_f": float,
            "condition_code": int (WMO code),
            "condition_description": str
        }
    
    Raises:
        httpx.HTTPError: on network failure, timeout, API error
        ValueError: on malformed response
    
    **Contract:**
    - Never returns partial data (all three fields or exception)
    - Temperature is Fahrenheit
    - Condition code is WMO standard
    - Condition description is looked up from WMO table
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                OPEN_METEO_BASE_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,weather_code",
                    "temperature_unit": "fahrenheit",
                }
            )
            response.raise_for_status()
    except httpx.HTTPError as e:
        logger.error(
            f"Failed to fetch weather from Open-Meteo for lat={latitude}, lon={longitude}: {e}"
        )
        raise

    data = response.json()
    
    # Parse current conditions from response
    current = data.get("current")
    if not current:
        raise ValueError(f"No 'current' field in Open-Meteo response: {data}")
    
    temperature_f = current.get("temperature_2m")
    condition_code = current.get("weather_code")
    
    if temperature_f is None:
        raise ValueError(f"No temperature in Open-Meteo response: {data}")
    if condition_code is None:
        raise ValueError(f"No weather_code in Open-Meteo response: {data}")
    
    # Look up condition description
    condition_description = WMO_CODES.get(condition_code, f"Unknown (code {condition_code})")
    
    return {
        "temperature_f": float(temperature_f),
        "condition_code": int(condition_code),
        "condition_description": condition_description,
    }


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9 / 5) + 32
