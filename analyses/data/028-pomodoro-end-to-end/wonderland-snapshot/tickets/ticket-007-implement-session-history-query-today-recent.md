## Ticket 007: Implement session history query (today + recent)

**Sources:** review-today-s-session-count-and-recent-activity
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: session-statistics-v1-week, session-statistics-all-time
- Blocked by: session-timer-backend, break-timer-backend
- Soft: —

**Description:**

Build a backend endpoint that returns all sessions completed today and a configurable window of recent sessions (e.g., last 7 days). Include session start time, end time, duration, and break duration if applicable. This is the data source for the today counter, recent activity view, and later statistics screens.

**Acceptance:**
- Endpoint returns all sessions from today with correct timestamps
- Endpoint returns sessions from a configurable prior window (default 7 days)
- Response includes session duration and break duration
- Response is ordered by recency (newest first)
- Query performance is acceptable for up to 100 sessions

**Risk:**

Large result sets if the user has been tracking sessions for weeks; consider pagination or a configurable limit.
