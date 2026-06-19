/**
 * NewsCard component.
 * 
 * Displays news headlines for the partner's location.
 * Accepts news object from dashboard API response.
 * 
 * Contract assumptions (from GET /api/dashboard response):
 * - news: {
 *     headlines: [
 *       { title: string, excerpt: string, source: string, url: string },
 *       ...
 *     ] | null,
 *     is_stale: bool (true if cache > 24 hours old),
 *     last_updated_at: ISO8601 string | null,
 *     error: 'not_yet_available' | 'unavailable' | 'degraded' | null
 *   }
 * 
 * UI states:
 * - loading: news is null (no data from API yet)
 * - ready: news object present, headlines present, error=null, is_stale=false
 * - stale: news object present, headlines present, is_stale=true (cache > 24h old)
 * - error-recoverable: error='not_yet_available' (polling hasn't run yet)
 * - error-unrecoverable: error='unavailable' (API has failed persistently, no cache)
 * - degraded: error='degraded' (cache exists but stale, shows headlines anyway)
 * 
 * Client state:
 * - None — component is fully stateless; all state comes from parent (Dashboard)
 * 
 * Notes:
 * - Renders top 3 headlines as a bulleted list
 * - Headlines are clickable links with target='_blank' + rel='noopener noreferrer'
 * - Freshness label uses last_updated_at to display "Last updated X hours ago"
 * - If is_stale=true (cache > 24h), label includes "(stale)" suffix
 * - If no headlines but error=null, shows fallback state (shouldn't happen per contract)
 */

interface Headline {
  title: string
  excerpt: string
  source: string
  url: string
}

interface NewsResponse {
  headlines: Headline[] | null
  is_stale: boolean
  last_updated_at: string | null
  error: 'not_yet_available' | 'unavailable' | 'degraded' | null
}

interface NewsCardProps {
  news: NewsResponse | null | undefined
  partnerName?: string
}

/**
 * Format ISO8601 timestamp to a human-readable "X hours ago" label.
 * Specifically designed for news freshness: always returns hours for clarity.
 */
function formatTimeAgo(isoString: string): string {
  try {
    const timestamp = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - timestamp.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    
    if (diffHours < 1) return '0 hours'
    if (diffHours === 1) return '1 hour'
    return `${diffHours} hours`
  } catch {
    return 'unknown'
  }
}

export default function NewsCard({ news, partnerName = "Partner" }: NewsCardProps) {
  // State: loading (no news data yet)
  if (!news) {
    return (
      <div className="card news-card">
        <h2>News</h2>
        <p className="loading-state">Loading news...</p>
      </div>
    )
  }

  // State: error-recoverable (not_yet_available: polling hasn't run yet)
  if (news.error === 'not_yet_available') {
    return (
      <div className="card news-card">
        <h2>News</h2>
        <p className="error-recoverable">
          News data not yet available. Polling will begin shortly.
        </p>
      </div>
    )
  }

  // State: error-unrecoverable (unavailable: persistent API failure, no cache)
  if (news.error === 'unavailable') {
    return (
      <div className="card news-card">
        <h2>News</h2>
        <p className="error-unrecoverable">
          News unavailable right now. Please try again later.
        </p>
      </div>
    )
  }

  // State: ready, stale, or degraded (data is present)
  if (news.headlines && news.headlines.length > 0) {
    return (
      <div className="card news-card">
        <h2>News</h2>
        <div className="news-card-content">
          <p className="partner-name">{partnerName}'s local news:</p>
          <ul className="headlines-list">
            {news.headlines.slice(0, 3).map((headline, index) => (
              <li key={index} className="headline-item">
                <a
                  href={headline.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="headline-link"
                  title={headline.excerpt}
                >
                  {headline.title}
                </a>
                <span className="headline-source">{headline.source}</span>
              </li>
            ))}
          </ul>
          {news.is_stale && news.last_updated_at && (
            <p className="stale-indicator">
              Last updated {formatTimeAgo(news.last_updated_at)} ago (stale)
            </p>
          )}
          {!news.is_stale && news.last_updated_at && (
            <p className="fresh-indicator">
              Last updated {formatTimeAgo(news.last_updated_at)} ago
            </p>
          )}
        </div>
      </div>
    )
  }

  // State: degraded with no headlines in cache (error='degraded' but no data to show)
  if (news.error === 'degraded') {
    return (
      <div className="card news-card">
        <h2>News</h2>
        <p className="error-recoverable">
          Latest news headlines are temporarily unavailable.
        </p>
      </div>
    )
  }

  // Fallback: no headlines and no error set (shouldn't happen per contract)
  return (
    <div className="card news-card">
      <h2>News</h2>
      <p className="loading-state">News data unavailable.</p>
    </div>
  )
}
