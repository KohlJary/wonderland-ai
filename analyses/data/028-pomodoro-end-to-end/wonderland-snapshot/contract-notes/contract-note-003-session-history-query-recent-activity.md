## Contract Note 003: Session history query & recent activity

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

N/A — proposing initial contract

**Proposed Change:**

API endpoint /sessions/history accepts optional params: since_timestamp (default: 7 days ago), limit (default: 50, max: 200). Returns array of {id, start_time, completed_at, duration_seconds, break_duration_seconds, break_skipped}. Ordered by completed_at DESC. Includes only completed sessions (state=completed). Today's count derived from this query with since_timestamp = today's midnight UTC.

**Source:** Feature 003 (today's count, recent timeline); ticket 007

**Frontend Impact (Tweedledee):**

Client caches query results per distinct (since_timestamp, limit) pair. For "today's sessions" view, cache with TTL=5min (or until user manually refreshes). For "7-day history" view, cache with TTL=30s (data less time-sensitive). Cache invalidates on session→completed event or on user manual refresh.

Client state: {historyCache: {[queryKey]: {sessions, fetchedAt}}, selectedTab: "today"|"week"}. Pagination not needed in v1 if we default limit=50 and assume users won't scroll beyond ~3 months of history. If users do, we can add pagination via offset in v2.

UI states: loading (initial fetch), loaded (displaying timeline), empty (no completed sessions in range), error-recoverable (fetch failed, show cached data if available + retry button). Stale state: if cache is stale and fetch is pending, show data with "updating..." indicator.

Open questions for pair:
1. Can client safely cache 50 sessions per query, or does user session volume make repeated requests necessary? (If yes, we may need pagination params: offset/limit instead of fixed 50.)
2. Does break_duration_seconds represent the *actual* break the user took, or the configured default? (Affects how we display "break with session" metadata.)
3. Is break_skipped a boolean, or do we need finer-grained break state (e.g., "skipped" vs "incomplete" vs "completed")?

**Backend Impact (Tweedledum):**

/sessions/history (user_id, since_timestamp, limit) returns sorted array of {id, start_time, completed_at, duration_seconds, break_duration_seconds, break_skipped}. Since_timestamp defaults to 7d ago UTC midnight. Limit defaults to 50, max 200. Results ordered by completed_at DESC. Index on (user_id, completed_at). No pagination offset in v1. Today's count derived by querying with since_timestamp = today's midnight UTC.
