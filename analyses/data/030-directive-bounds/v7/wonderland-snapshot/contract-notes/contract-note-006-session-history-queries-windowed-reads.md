## Contract Note 006: Session history queries (windowed reads)

**State:** agreed
**Contract Version:** v1 (history-windowed-reads)

**Current Shape:**

Query endpoints for session history: (1) today's count (sessions completed in last 24h), (2) weekly history (last 7 days, per-day aggregates), (3) all-time history (lifetime count + total_seconds). Each query returns session records with: session_id, start_timestamp, end_timestamp, duration_seconds, phase_completed (focus|break). Frontend needs: pagination on all-time (lazy-load as user scrolls), caching with TTL (5 min), error handling for network failures.

**Agreed Changes:**

Query endpoints for session history as proposed. This is substantively the same as contract-003 (history query shape), with additional detail on implementation expectations.

**Frontend Impact (Tweedledee):**

I'll fetch and cache history on app startup and on explicit user refresh. Views: (1) today's card (centered big session count + total focus time), (2) weekly page (7-day calendar grid, per-day aggregates), (3) all-time page (infinite scroll, per-session rows). Each row displays: start_timestamp, end_timestamp, duration, phase. Rows are tappable for detail view if needed. Caching: 5-minute TTL, invalidate on new session completion (I'll clear the cache after POSTing a completion event). Error handling: show cached data with 'data may be stale' indicator if query fails; retry on next user action or after 30 seconds.

**Backend Impact (Tweedledum):**

Backend provides GET /sessions?window=today|week|all-time endpoints (as per contract-003). Each query returns a list of session records filtered by user_id and time window. Response includes: sessions (list of session records), session_count (int), total_focus_seconds (int), window_start (ISO8601), window_end (ISO8601). Pagination deferred to v2 (see contract-003 notes).

**Agreed By:** Tweedledee and Tweedledum (resolved in test-scenarios thread)
**Date:** M4, test-scenarios

**Notes:**

This contract and contract-003 are almost identical. Both are marked agreed and reference the same implementation contract. The details here (per-day aggregates for weekly, infinite scroll for all-time) are frontend UI concerns, not backend contract requirements.
