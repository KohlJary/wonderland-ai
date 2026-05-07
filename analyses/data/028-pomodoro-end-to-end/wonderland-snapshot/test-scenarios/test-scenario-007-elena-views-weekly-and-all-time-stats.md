## Scenario: Elena checks her weekly total and all-time total to understand focus capacity

**Severity:** breakage

**Setup:**
Elena has been using the app for 6 months. She's completed 200 sessions total, with 8 this week.
She opens the Statistics section on Sunday evening.

**Trigger:**
Elena taps the "This Week" tab to see her weekly aggregate, then taps "All-Time" to see her progress over 6 months.

**Expected:**
1. "This Week" tab shows:
   - Total sessions: 8
   - Total focus time: 200 minutes (or 3h 20m)
   - Week start and end dates (Mon–Sun)
2. "All-Time" tab shows:
   - Total sessions: 200
   - Total focus time: 5,000 minutes (or 83h 20m)
3. Optional: a graph or timeline showing weekly averages over the past 12 weeks
4. All values update immediately if Elena completes another session while viewing

**Concern:**
This is breakage because tracking and trends are core to Elena's use case. Without working stats:
- Elena can't verify that her focus capacity is improving
- She can't spot patterns (e.g., "I focus best on Tuesdays")
- She can't celebrate progress (a key motivator for habit-tracking apps)
- The product fails its enrichment value for long-term users

Broken stats = broken long-term user experience.

**Property:**
For any user U with N completed sessions:
- GET /stats/week returns {session_count: C, total_duration_seconds: D, week_start_date, week_end_date}
  where C = count of sessions completed in current week (Mon–Sun UTC)
  and D = sum of duration_seconds for those sessions
- GET /stats/all-time returns {session_count: N, total_duration_seconds: D_total}
  where D_total = sum of duration_seconds for all sessions ever
- Both endpoints compute fresh on each request (no stale data)

**Implies:**
- Implies backend: optimize session queries on (user_id, completed_at) for speed
- Implies frontend: cache stats with reasonable TTL (60s per contract) but always recompute on visible change
- Implies design: decide whether to include optional historical graph in v1 or defer to v2
