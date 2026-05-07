## Test Scenario: History aggregates must be computed correctly

**Severity:** high

**Feature:** Feature-002 (Review session history and persistence across restarts)

**Setup:**

User completes 2 focus sessions (1500 seconds each) and 2 break sessions (300 seconds each), all within today's date range.

Sessions:
- Session 1 (focus): 1500 sec
- Session 2 (break): 300 sec
- Session 3 (focus): 1500 sec
- Session 4 (break): 300 sec

**Trigger:**

User queries GET /sessions?window=today

**Expected:**

Response includes:
```json
{
  "session_count": 4,
  "total_focus_seconds": 3000,
  "sessions": [...]
}
```

Note: `session_count` includes all sessions (focus + break). `total_focus_seconds` includes only focus sessions (not breaks).

**Concern:**

Incorrect aggregates are "silent wrongness" — the backend returns numbers, and they *look* credible, but they're wrong. The user sees "4 sessions / 200 minutes" when they actually logged "50 minutes" of focused work. This breaks trust in the entire system. More insidiously, the user may not notice the error until they try to export history for a client, at which point the proof-of-work is already inaccurate.

**Property:**

For any history window:
- `session_count` = number of sessions of any type (focus or break)
- `total_focus_seconds` = sum of `focus_duration_seconds` for sessions where `session_type='focus'`
- `total_focus_seconds` excludes break sessions, regardless of their duration

**Mechanism:**

Backend aggregation query must filter by session_type when computing total_focus_seconds:
```sql
SELECT COUNT(*) as session_count,
       SUM(CASE WHEN session_type='focus' THEN focus_duration_seconds ELSE 0 END) as total_focus_seconds
FROM sessions
WHERE user_id = ? AND completed_at BETWEEN window_start AND window_end
```

**Runnable Tests:**

- `tests/test_feature_002_edge_cases.py::test_feature_002_history_aggregates_correctness`
