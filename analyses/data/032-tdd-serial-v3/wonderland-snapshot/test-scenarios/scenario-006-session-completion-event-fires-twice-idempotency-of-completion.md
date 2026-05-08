## Scenario 006: Session completion event fires twice (idempotency of completion)

**Severity:** silent-wrongness

**Setup:**

Focus session at 25 minutes. Timer reaches 0. Completion event emitted. Network glitch causes retry.

**Trigger:**

POST /sessions/log fires twice with same payload within seconds.

**Expected:**

First completes. Second returns 409 (already completed) or idempotent 200 (no change). Daily history counts session exactly once.

**Concern:**

If not idempotent, Marcus's daily total shows 50 min instead of 25. Session appears twice in history. Silent wrongness — user won't notice until inspecting history.

**Property:**

POST /sessions/log is idempotent per contract-005.

**Implies:**
- Covered by contract-005 idempotency guarantee.
- Requires daily history aggregation to count correctly — contract-004.
