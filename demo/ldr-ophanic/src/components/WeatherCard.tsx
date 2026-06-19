/**
 * WeatherCard component.
 * 
 * Displays weather data for the partner's location.
 * Accepts weather object from dashboard API response.
 * 
 * Contract assumptions (from GET /api/dashboard response):
 * - weather: {
 *     current_conditions: string | null (e.g., "Partly Cloudy"),
 *     temp_f: number | null (e.g., 72.5),
 *     is_stale: bool (true if cache > 90 minutes old),
 *     last_updated_at: ISO8601 string | null,
 *     error: 'not_yet_available' | 'unavailable' | 'degraded' | null
 *   }
 * 
 * UI states:
 * - loading: weather is null (no data from API yet)
 * - ready: weather object present, error=null, is_stale=false
 * - stale: weather object present, is_stale=true, error='degraded'
 * - error-recoverable: error='not_yet_available' (polling hasn't run yet)
 * - error-unrecoverable: error='unavailable' (API has failed persistently)
 * 
 * Client state:
 * - None — component is fully stateless; all state comes from parent (Dashboard)
 */

interface WeatherResponse {
  current_conditions: string | null
  temp_f: number | null
  is_stale: boolean
  last_updated_at: string | null
  error: 'not_yet_available' | 'unavailable' | 'degraded' | null
}

interface WeatherCardProps {
  weather: WeatherResponse | null | undefined
  partnerName?: string
}

/**
 * Format ISO8601 timestamp to a human-readable "X minutes/hours ago" label.
 */
function formatTimeAgo(isoString: string): string {
  try {
    const timestamp = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - timestamp.getTime()
    const diffMinutes = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMinutes / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMinutes < 1) return 'just now'
    if (diffMinutes < 60) return `${diffMinutes}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  } catch {
    return 'unknown'
  }
}

export default function WeatherCard({ weather, partnerName = "Partner" }: WeatherCardProps) {
  // State: loading (no weather data yet)
  if (!weather) {
    return (
      <div className="card weather-card">
        <h2>Weather</h2>
        <p className="loading-state">Loading weather...</p>
      </div>
    )
  }

  // State: error-recoverable (not_yet_available: polling hasn't run yet)
  if (weather.error === 'not_yet_available') {
    return (
      <div className="card weather-card">
        <h2>Weather</h2>
        <p className="error-recoverable">
          Weather data not yet available. Polling will begin shortly.
        </p>
      </div>
    )
  }

  // State: error-unrecoverable (unavailable: persistent API failure)
  if (weather.error === 'unavailable') {
    return (
      <div className="card weather-card">
        <h2>Weather</h2>
        <p className="error-unrecoverable">
          Couldn't load weather right now. Please try again later.
        </p>
      </div>
    )
  }

  // State: ready or stale (data is present)
  if (weather.temp_f !== null && weather.current_conditions) {
    return (
      <div className="card weather-card">
        <h2>Weather</h2>
        <div className="weather-card-content">
          <p className="partner-name">{partnerName}'s weather:</p>
          <p className="weather-display">
            <span className="temperature">{Math.round(weather.temp_f)}°F</span>
            <span className="condition">{weather.current_conditions}</span>
          </p>
          {weather.is_stale && weather.last_updated_at && (
            <p className="stale-indicator">
              Last updated {formatTimeAgo(weather.last_updated_at)}
            </p>
          )}
          {!weather.is_stale && weather.last_updated_at && (
            <p className="fresh-indicator">
              Updated {formatTimeAgo(weather.last_updated_at)}
            </p>
          )}
        </div>
      </div>
    )
  }

  // Fallback: data is null but no error set (shouldn't happen per contract)
  return (
    <div className="card weather-card">
      <h2>Weather</h2>
      <p className="loading-state">Weather data unavailable.</p>
    </div>
  )
}
