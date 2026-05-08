## Scenario 019: Break completion at midnight logs to correct date (timezone seam)

**Severity:** silent-wrongness

**Setup:**

Break starts 2025-01-14T23:55:00Z (5 min before midnight), duration 600s, completes 2025-01-15T00:05:00Z (5 min after).

**Trigger:**

POST /sessions/log with completed_at='2025-01-15T00:05:00Z'. Keisha checks daily summaries.

**Expected:**

Break appears in exactly one daily summary: 2025-01-15 (completion-date bucketing, per contract).

**Concern:**

Midnight is seam. Naive bucketing by start_time puts break in yesterday's summary. TZ confusion causes sessions to vanish. Hatter tests calendar boundaries because most teams test 9-to-5.

**Property:**

For break B with start=S and completion=C on different dates (UTC), B appears in GET /daily/summary?date=C (not S). Duration counted exactly once.

**Implies:**
- Implies contract must clarify: bucketing by start_time, completion_time, or local-TZ midnight? Must be consistent.
- Dormouse tracks production breaks disappearing from summaries — often TZ or date-boundary bug.
- If local-TZ support added later, bucketing must be consistent (always UTC or always local).
