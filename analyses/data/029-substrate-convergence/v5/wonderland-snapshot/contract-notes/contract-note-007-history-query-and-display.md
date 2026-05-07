## Contract Note 007: History query and display

**State:** agreed
**Contract Version:** v1 (Three query endpoints: /api/sessions/today, /api/sessions?from_date=...&to_date=...&limit=50&offset=0, /api/sessions/stats?period=week|all_time. Indexed on (user_id, started_at) desc. Stats pre-computed on write.)

**Current Shape:**

No contract yet; establishing baseline

**Proposed Change:**

Backend exposes /api/sessions/today (completed sessions for current date), /api/sessions/week (current week), /api/sessions (all-time, paginated). Each session record: {id, started_at, completed_at, duration_ms, was_break: bool}. Frontend fetches on app load and caches; refetch on session completion.

**Source:** feature-003 (view session history and statistics)

**Frontend Impact (Tweedledee):**

pending

**Backend Impact (Tweedledum):**

Your notes leave the query shape open. Let me propose concrete: GET /sessions/today returns sessions where started_at falls in calendar day (user's local date, timezone-normalized on frontend; backend just compares dates). GET /sessions/week returns sessions in ISO week. GET /sessions returns all-time with pagination (limit=50 default, offset=0; last_key for cursor-based if you prefer). Each record: {id, started_at, completed_at, duration_seconds, break_completed_at}. Stats query: GET /sessions/stats?period=week|all_time returns {total_count, avg_per_day, days: [{date, count}, ...]}. All queries indexed on (user_id, started_at) descending for < 100ms latency even with 10k sessions. Pre-computed counters on write for stats endpoint (increment daily bucket on session complete).

**Resolution:**

Unified v1 from Dum 002 + Dee 007. Locked.
