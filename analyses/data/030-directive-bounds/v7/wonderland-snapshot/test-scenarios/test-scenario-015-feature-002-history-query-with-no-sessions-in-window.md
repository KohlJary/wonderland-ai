## Test Scenario: History query returns empty window gracefully

**Severity:** curiosity (but affects UX)

**Feature:** Feature-002 (history queries)

**Setup:**

Jordan starts using the app fresh. On day 1, they immediately query GET `/sessions?window=all-time` without starting any sessions yet. On day 7, they query `/sessions?window=week` without having started any sessions in the past week (all sessions were 2+ weeks ago).

**Trigger:**

Two queries:
1. GET /sessions?window=all-time (no sessions exist yet)
2. GET /sessions?window=week (no recent sessions)

**Expected:**

Both return 200 OK with:
```json
{
  "window": "all-time" | "week",
  "sessions": [],
  "session_count": 0,
  "total_focus_seconds": 0,
  "window_start": "...",
  "window_end": "..."
}
```

Frontend displays gracefully: "You haven't logged any sessions yet. Start a session to get started!" (not an error, not a blank screen).

**Concern:**

Possible failures when history is empty:
1. **Null pointer exception:** Backend tries to calculate min(completed_at) for window_start, crashes because no sessions exist
2. **Division by zero:** Backend calculates average focus time by dividing total by session_count; when session_count=0, crashes
3. **Malformed response:** Backend returns null for sessions instead of empty array; frontend crashes on len(null)
4. **Invalid window bounds:** window_start and window_end are nonsensical when no sessions exist (e.g., both are epoch 0)
5. **Missing fields:** Response is missing expected fields (sessions, window_start, etc.) when empty

**Property:**

For any query window (today, week, all-time) with zero sessions:
- sessions is an empty array (not null, not missing)
- session_count == 0
- total_focus_seconds == 0
- window_start and window_end are valid ISO8601 timestamps (representing the correct time window, even if empty)
- Response is 200 OK (not 404, not 204 No Content)

**Mechanism:**

Backend should:
1. Construct the window bounds (window_start, window_end) **before** querying sessions, not based on session data
2. Check if result set is empty and return empty array, not null
3. Initialize aggregates to 0 before summing; if no rows, return 0 (not null, not missing)
4. Test the empty case explicitly (don't assume it's covered by non-empty tests)

**Implies:**

- Frontend needs explicit handling for empty history (show a "get started" prompt, not blank space)
- This is a common UX failure: empty states are often overlooked in testing

**Runnable Tests:**

- `tests/test_feature_002_empty_history.py::test_all_time_window_empty_returns_zero_counts`
- `tests/test_feature_002_empty_history.py::test_today_window_empty_returns_zero_counts`
- `tests/test_feature_002_empty_history.py::test_empty_window_response_shape_is_valid`
