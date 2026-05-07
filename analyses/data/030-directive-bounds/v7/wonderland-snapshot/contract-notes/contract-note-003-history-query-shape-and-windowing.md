## Contract Note 003: History query shape and windowing

**State:** agreed
**Contract Version:** v1 (history-query-windowing)

**Current Shape:**

GET /sessions?window=today|week|all-time returns: { sessions: [{ session_id, session_type, focus_duration_seconds, break_duration_seconds, started_at, completed_at }, ...], window, total_focus_seconds (aggregated), session_count (int), window_start (ISO8601), window_end (ISO8601) }.

**Agreed Changes:**

History query shape and windowing as proposed. Frontend calls GET /sessions?window=today|week|all-time on app startup and on explicit user refresh. Backend computes aggregates (sum of focus_duration_seconds, count of sessions) per query. Window definitions: "today" = last 24 hours from now; "week" = last 7 days; "all-time" = all records.

**Frontend Impact (Tweedledee):**

Frontend calls GET /sessions?window=today|week|all-time on app startup and on explicit user refresh. I'll cache responses for 5 minutes (subsequent calls within 5 min return cached data; manual refresh bypasses cache). For all-time window, I'll accept that backend returns all records (no pagination in v1; if query becomes slow, pagination can be added later without breaking the contract). I'll render today's aggregates as a hero card (big session count + total focus time in minutes), weekly as a 7-day calendar grid (per-day aggregates), all-time as infinite-scroll rows (one row per session, newest first). Your pre-aggregated total_focus_seconds and session_count are exactly what I need — no client-side re-aggregation. On network failure, I'll show cached data with 'may be stale' badge, or error state if no cache exists.

**Backend Impact (Tweedledum):**

Backend queries immutable session facts filtered by (user_id, time window). Aggregates are computed per query (sum of focus_duration_seconds for window, count of sessions). Sessions in the response are ordered by completed_at (newest first). Window boundaries are defined as: "today" = now - 24 hours to now; "week" = now - 7 days to now; "all-time" = all records for user. Session records include: session_id, session_type, focus_duration_seconds, break_duration_seconds, started_at, completed_at.

**Agreed By:** Tweedledee and Tweedledum (resolved in test-scenarios thread)
**Date:** M4, test-scenarios

**Notes:**

Pagination deferred: v1 does not include limit/offset params. If query performance becomes a concern in testing, pagination can be added as a future contract update.

Aggregation consistency: because sessions are immutable facts, aggregates are always consistent (no racing writes to sessions). Caching is safe; cached data is valid until new sessions arrive.
