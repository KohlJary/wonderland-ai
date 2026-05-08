## Test Scenario 005: Break completion at midnight logs to correct date

**Severity:** silent-wrongness

**Setup:**

A break session starts on 2025-01-14 at 23:55:00 UTC with duration=600 seconds (10 minutes). It completes on 2025-01-15 at 00:05:00 UTC (10 seconds past midnight).

**Trigger:**

The frontend POSTs /sessions/log with:
```json
{
  "type": "break",
  "duration_configured_seconds": 600,
  "duration_actual_seconds": 600,
  "completed_at": "2025-01-15T00:05:00Z"
}
```

Later, Keisha checks her daily summaries for 2025-01-14 and 2025-01-15.

**Expected:**

The break session appears in exactly one daily summary:
- EITHER 2025-01-14 (start date) 
- OR 2025-01-15 (completion date)

The contract must be clear which one. The scenario here assumes completion-date bucketing (standard in most analytics), so the break should appear in 2025-01-15's summary.

**Concern:**

Midnight is a seam. Most systems test "happy clock" scenarios (9 AM to 5 PM) and miss the boundary. Here's what happens with naive bucketing:

- If you bucket by start_time, breaks that cross midnight appear in yesterday's summary. User adds two 5-minute breaks on 2025-01-15 and expects 10 minutes; instead, one appears in 2025-01-14 because it started the night before.
- If you bucket by completion_time (correct), you must ensure the backend's "today" calculation matches the frontend's. Off-by-one errors in TZ handling cause the session to vanish from summaries.
- If you use local TZ instead of UTC, midnight happens at different absolute times depending on the user's location. A break completed at 2025-01-15T04:05:00Z might be "yesterday" if the user is in timezone -5:00.

**Property:**

For any break session B with start_time=S and completion_time=C where S and C are on different calendar dates (in UTC):
- B appears in GET /daily/summary?date=C (completion date), not in GET /daily/summary?date=S
- B's duration is counted exactly once across all daily summaries

Corollary: If local TZ support is added later, the bucketing rule must be consistent (always UTC, or always local TZ — not mixed).

**Implies:**

This is a contract clarification test. The backend and frontend must agree on the bucketing rule. Dormouse should track production cases where breaks "disappear" from daily summaries; it's often a TZ or date-boundary bug. Caterpillar should review the daily-summary query to ensure it buckets correctly.

Also: this is the Hatter's timezone seam. It's deceptively complex and often overlooked. The test here is simple; the implications are subtle.
