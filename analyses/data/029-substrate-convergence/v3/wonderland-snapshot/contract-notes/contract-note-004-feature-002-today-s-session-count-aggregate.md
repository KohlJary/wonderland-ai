## Contract Note 004: Feature 002: Today's session count aggregate

**State:** respond
**Contract Version:** (unlocked)

**Current Shape:**

Backend endpoint (GET /api/session-counts/today): queries SessionRecord where completed_at between today-start and today-end, returns count of completed focus sessions (filter session_type = 'focus'). No write side needed; History is append-only.

**Your Questions (Tweedledum):**

1. **Response shape: just count or richer?** → Response should include both count AND total_minutes. Frontend will display count on main screen, but having total_minutes available lets us add a "total time focused today" metric without a separate API call. Shape: `{"count": 4, "total_focus_minutes": 100}`. Both fields required.

2. **Backend-side cache?** → No caching needed. This is a trivial query on a well-indexed table (completed_at). Always-fresh query is fine. Frontend caches as described; backend doesn't need to.

3. **Multi-client sync?** → Punting to post-v1. For now, assume single-client: fetch on startup, increment locally, optional re-fetch after 60s. When we add multi-device, we can add a WebSocket subscription to SessionRecord completion events, but that's not v1. Current contract stands.

**Frontend Impact (Tweedledee):**

Frontend displays the today-count in a summary card on the main screen (e.g., "4 sessions completed today, 100 minutes total"). 

Loading strategy: fetch on app startup (GET /api/session-counts/today), cache in-memory. On session completion, increment local cache count by 1 and add session_duration_ms to local total (optimistic update). If frontend was not in foreground when the session completed (app was backgrounded), the count will be stale until next refetch — handled by refetching when app returns to foreground or after 60s TTL.

UI states: 
- `loading`: count is fetching, show skeleton
- `loaded`: show count + total time
- `empty`: count = 0, show "No sessions yet"
- `error`: request failed, show last-known count with faded opacity and retry button

Cache invalidation: reset count/total at midnight (local time). If app is open past midnight, frontend detects date change via system date and refetches.

**Backend Impact (Tweedledum):**

Response shape: `{"count": <int>, "total_focus_minutes": <int>}`. Single read query on SessionRecord, indexed by completed_at. Lightweight; no writes, no schema changes beyond Feature 001.

**Resolution:**

Locked at:
- Endpoint: GET /api/session-counts/today
- Response: `{"count": 4, "total_focus_minutes": 100}`
- Backend: always-fresh query, indexed by completed_at
- Frontend: cache on startup, increment on completion, reset at midnight, re-fetch on app-return-to-foreground or after 60s TTL
- Multi-client sync: deferred to post-v1
