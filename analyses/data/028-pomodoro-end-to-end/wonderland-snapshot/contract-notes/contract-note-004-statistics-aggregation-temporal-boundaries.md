## Contract Note 004: Statistics aggregation & temporal boundaries

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

N/A — proposing initial contract

**Proposed Change:**

API endpoints /stats/week and /stats/all-time. /stats/week returns {session_count, total_duration_seconds, week_start_date, week_end_date}. /stats/all-time returns {session_count, total_duration_seconds}. Week boundary is Mon–Sun UTC (configurable per user settings in future, hardcoded to UTC Mon–Sun for v1). Both endpoints compute from Sessions WHERE state='completed'. Week boundary logic: week_start = date(completed_at) - ((date(completed_at) - Monday) % 7 days). Aggregations are computed on-the-fly; no pre-computed stats table in v1.

**Source:** Feature 004 (weekly & all-time stats); tickets 009-010

**Frontend Impact (Tweedledee):**

Client caches stats with TTL=60s. Cache updates: (a) automatically every 60s if stats view is visible, (b) immediately after session→completed event, (c) on manual refresh. Stats typically displayed as dashboard widgets (small, always-visible) and detailed stats page (full view). No client-side aggregation; all calc is server-side.

Client state: {stats: {weekly: {session_count, total_duration_seconds, week_start_date, week_end_date}, all_time: {session_count, total_duration_seconds}, fetchedAt}}. 

UI states: loading (initial fetch), loaded (displaying numbers), empty (user has 0 sessions), error-recoverable (fetch failed, show cached data + retry).

Open questions for pair:
1. Does /stats/week accept an optional week_start_date param to query historical weeks, or is it always current week?
2. What is week_end_date's semantics? (Inclusive or exclusive? For display, we need to know if "week ending 2024-01-14" includes sessions from 2024-01-14 23:59 or only up to 2024-01-13 23:59.)
3. For all-time stats, should we return membership_duration_days alongside total_duration_seconds, so frontend can compute average session/day?

**Backend Impact (Tweedledum):**

/stats/week computes current Mon–Sun UTC window only (no historical param in v1). Boundaries inclusive: Mon 00:00 UTC through next Mon 00:00 UTC. Returns {session_count, total_duration_seconds, week_start_date, week_end_date}. /stats/all-time returns {session_count, total_duration_seconds, membership_duration_days}. Membership_duration_days = floor((now - user.launch_date) / 86400). On-the-fly aggregation; index on (user_id, completed_at).
