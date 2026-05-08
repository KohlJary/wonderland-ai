## Scenario 034: Concurrent completions at midnight: Session A at 23:59:59.999, Session B at 00:00:00.001, both recorded

**Severity:** degradation

**Setup:**

Derek: two timers open (bug possible). A completes Mon 23:59:59.999. B completes Tue 00:00:00.001 (1ms apart). Both hit backend simultaneously.

**Trigger:**

Both completions processed. Streak query runs.

**Expected:**

Both recorded with correct timestamps (A=Mon, B=Tue). Streak sees both.

**Concern:**

If streak calc not transactionally protected, small window for partial-state queries. Unlikely visible bug (1-sec inconsistency won't show) but worth documenting.

**Property:**

Streak calculation (a) synchronous per request (no race), (b) transactionally protected, or (c) documented as eventually consistent.

**Implies:**
- Implies backend perf test: streak query <100ms
- Implies clarification: synchronous on-request or background job?
