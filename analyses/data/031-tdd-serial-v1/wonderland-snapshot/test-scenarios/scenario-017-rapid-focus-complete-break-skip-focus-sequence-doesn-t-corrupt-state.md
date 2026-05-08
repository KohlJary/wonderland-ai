## Scenario 017: Rapid focus-complete-break-skip-focus sequence doesn't corrupt state

**Severity:** silent-wrongness

**Setup:**

User rapidly cycles: start focus (5s) -> wait -> skip break -> start focus. All within 30 seconds. Client polls for session state after each step.

**Trigger:**

Sequence: POST start focus, wait 5s, POST skip break (auto-started), POST start focus. Each call succeeds.

**Expected:**

After each step, exactly one session has status='running'. No orphaned sessions (status=NULL or undefined). Session IDs unique. Each session has correct type and duration_seconds.

**Concern:**

Under rapid transitions, backend might not clean up old session records. Client might cache stale state. Silent wrongness: API returns correct per-call, but accumulated records corrupt the state view.

**Property:**

After each session transition, exactly one session has status='running'. All previous sessions have status='completed'.
