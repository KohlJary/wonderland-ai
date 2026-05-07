## Test Scenario 019: Weekly history includes only the past 7 days, not more, not less

**Severity:** silent-wrongness

**Feature:** Feature 003: Inspect historical session data across weeks and all-time

**Setup:**

Yuki has been using the timer for 10 days. She has completed sessions on each day:
- Day 1 (Jan 6): 3 sessions, 75 minutes
- Day 2 (Jan 7): 4 sessions, 100 minutes
- ...
- Day 8 (Jan 13): 2 sessions, 50 minutes (8 days ago from "today" Jan 15)
- Day 9 (Jan 14): 5 sessions, 125 minutes (1 day ago)
- Day 10 (Jan 15): 2 sessions, 50 minutes (today)

Today is January 15th. Yuki opens the "This Week" view and fetches GET /api/session-history/weekly.

**Expected:**

The response should include data for only the past 7 days (Jan 9–Jan 15, inclusive):
- Jan 9: 0 sessions (or omitted if no data)
- Jan 10: 0 sessions
- ...
- Jan 13: 2 sessions, 50 minutes
- Jan 14: 5 sessions, 125 minutes
- Jan 15: 2 sessions, 50 minutes

Sessions from Jan 6–8 should NOT be included in the weekly response. They should only appear in the all-time view.

**Concern:**

If the backend's "past 7 days" calculation is off by a day (e.g., it includes the past 8 days, or only the past 6 days), the weekly view will show incorrect data. Over time, as the user builds a history, they might not notice the boundary is wrong until they compare the weekly view with a manual count.

Also, if the frontend caches the weekly data and doesn't refetch when the boundary shifts (e.g., when a day rolls off the 7-day window), the displayed data will become stale.

**Property:**

For all calls to GET /api/session-history/weekly at time T:
  data includes SessionRecords where completed_at >= (T - 7 days) AND completed_at < (T + 1 day)
  data excludes SessionRecords where completed_at < (T - 7 days)

The window is exactly 7 days, not more, not less.

**Implies:**

This tests the date range filtering in the historical aggregation queries (contract-note-006). The boundary is a critical seam between "this week" and "older history."

