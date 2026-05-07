## Contract Note 003: Settings persistence and application

**State:** agreed
**Contract Version:** v1 (GET /api/settings, PUT /api/settings with {session_duration_seconds?, break_duration_seconds?}. Bounds [60s, 7200s]. Frontend caches at session init; changes apply to *next* session only. Endpoint returns {session_duration_seconds, break_duration_seconds, settings_updated_at}.)

**Current Shape:**

undefined

**Proposed Change:**

Settings table: id (uuid), user_id (fk), session_duration_seconds (default 1500 = 25 min), break_duration_seconds (default 300 = 5 min), updated_at. GET /settings returns current settings (synchronous, < 10ms). PUT /settings (body: {session_duration_seconds?, break_duration_seconds?}) validates bounds (1 min <= duration <= 120 min, per story 005 acceptance), writes and returns new settings. Settings apply immediately to the next timer start — no mid-timer change. Frontend reads settings on app launch and caches locally; re-fetches on explicit settings save or on app resume from background.

**Source:** Story 005 (customize durations) and feature 004

**Frontend Impact (Tweedledee):**

Clarify: does the frontend need to display 'current settings version' to the user, or is internal caching at session start sufficient?

**Backend Impact (Tweedledum):**

Settings update is timestamped (settings_updated_at). Endpoint returns both the new settings AND the timestamp, so frontend can cache-on-session-start and reason about 'this session was governed by settings version X from timestamp Y'.

**Resolution:**

Frontend reads settings on app launch and caches locally; re-fetches on explicit settings save or app resume. New settings govern next session, not current one. Settings versioning timestamp allows frontend to reason about which settings governed which session.
