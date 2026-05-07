## Test Scenario: History window boundaries must not leak sessions across windows

**Severity:** high

**Feature:** Feature-002 (Review session history and persistence across restarts)

**Setup:**

User has 1 session recorded 8 days ago, and 1 session recorded 3 days ago.

- Session A: started_at=2024-01-07T10:00:00Z, completed_at=2024-01-07T10:25:00Z
- Session B: started_at=2024-01-12T10:00:00Z, completed_at=2024-01-12T10:25:00Z

Today is 2024-01-15.

**Trigger:**

User queries:
- GET /sessions?window=week (last 7 days = Jan 8 to Jan 15)
- GET /sessions?window=all-time (all records)

**Expected:**

- GET /sessions?window=week returns session_count=1 (only Session B at Jan 12)
  - Session A (Jan 7) is excluded because it's more than 7 days ago
- GET /sessions?window=all-time returns session_count=2 (both sessions)

**Concern:**

Window boundary bugs are silently wrong. If the backend accidentally includes Session A in the week query, the user sees inflated metrics ("This week I did 2 sessions" when they actually did 1 this week). Conversely, if the backend accidentally excludes a session that should be included, the user's proof-of-work is incomplete.

The boundary is especially fragile around the "week" window definition. Is it:
- Last 7 calendar days?
- Last 7 * 24 hours?
- Monday-to-Sunday of the current week?

All three give different results depending on the current day and time. The contract must specify exactly.

**Property:**

For any history window, the set of returned sessions must:
1. Include all sessions whose `completed_at` falls within the window time range
2. Exclude all sessions whose `completed_at` falls outside the window time range
3. Not double-count any session (each appears at most once)

Window definitions:
- "today" = last 24 hours from now (from `datetime.now() - timedelta(hours=24)` to `datetime.now()`)
- "week" = last 7 days from now (from `datetime.now() - timedelta(days=7)` to `datetime.now()`)
- "all-time" = no bounds (all sessions for the user, ordered by completed_at descending)

**Mechanism:**

Backend filters by `completed_at` (not `started_at`), using the exact window bounds above. A session that spans a boundary (started before, completed after) is included or excluded based solely on its `completed_at`.

**Runnable Tests:**

- `tests/test_feature_002_edge_cases.py::test_feature_002_history_week_window_boundary`
- `tests/test_feature_002_edge_cases.py::test_feature_002_history_all_time_large_dataset`
