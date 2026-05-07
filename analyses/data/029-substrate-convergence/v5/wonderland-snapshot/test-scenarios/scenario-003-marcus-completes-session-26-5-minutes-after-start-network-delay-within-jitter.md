## Scenario 003: Marcus completes session 26.5 minutes after start (network delay, within jitter)

**Severity:** silent-wrongness

**Setup:**

Marcus started session 26.5 minutes ago. /complete request delayed by network latency.

**Trigger:**

Frontend POSTs /complete with completed_at = started_at + 1590 seconds (90 seconds late).

**Expected:**

Backend accepts if jitter ≥ 90 seconds. Session persists with accurate timestamp.

**Concern:**

If jitter too tight, normal latency causes rejections and data loss. If too loose, durations become unreliable. Threshold is essential.

**Property:**

Backend accepts completed_at ≤ started_at+duration_seconds+jitter. Rejects beyond that. Jitter must accommodate typical network latency (~5-10 seconds).

**Implies:**
- Test file: tests/test_sessions_lifecycle.py
