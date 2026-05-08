## Contract Note 007: Session history retrieval for daily view

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

None — v1 negotiation

**Proposed Change:**

Frontend GET /sessions?date=YYYY-MM-DD (timezone interpretation TBD). Backend returns [ { "session_id", "type": "focus"|"break", "duration_configured_seconds", "duration_actual_seconds", "completed_at": ISO8601 }, ... ]. Frontend renders daily view, polls every 10s, calculates aggregates (total focus time, session counts).

**Source:** Feature 003 (daily review). Feature 002 may query to confirm prior session was focus (auto-start-break logic).

**Frontend Impact (Tweedledee):**

Daily view component fetches on mount and every 10s while visible. I render session list (timestamp, type, duration) and aggregates (total focus, count, etc.). I calculate all aggregates from returned data; no analytics backend calls.

**Backend Impact (Tweedledum):**

Backend provides GET /sessions?date=YYYY-MM-DD returning array of session records: [ { session_id, type, duration_configured_seconds, duration_actual_seconds, completed_at }, ... ]. Query: I index session_log (user_id, DATE(completed_at)) for fast lookups. Timezone: I interpret ?date as user's local date. This requires either (a) user timezone in settings (backend doesn't have it v1, so frontend must pass it as query param), or (b) I assume UTC and frontend converts dates locally before querying. I recommend (b) for v1 — frontend builds the query using UTC midnight-to-midnight boundaries. Response includes all sessions for that UTC date; frontend renders. No polling needed; response is full daily snapshot. If real-time updates are needed later (v2), I'd emit session-logged events; for now, frontend polls if needed, I serve each query in <100ms.
