## Scenario 003: Concurrent PATCHes to same session race safely; last-write-wins without error

**Severity:** silent-wrongness

**Setup:**

Session in progress, open in two browser tabs. Real time: 20 min elapsed, 5 remaining. Tab 1 sends PATCH {completionStatus:'completed', actualDuration:20} at 24:50. Tab 2 sends PATCH {completionStatus:'completed', actualDuration:25} at 24:55.

**Trigger:**

Both PATCHes arrive at backend milliseconds apart.

**Expected:**

Both return 200 OK (no 409 Conflict). Final state determined by last-write-wins (full replacement, not merge). Tab 2's value wins: actualDuration=25. Both tabs eventually converge to final state.

**Concern:**

Backend uses READ-MODIFY-WRITE without concurrency control. Race condition: both read same baseline, apply delta, write, second overwrites first. Or merges them (actualDuration=[20,25]), corrupting record. Or returns 409 Conflict (wrong for M1, requires retry logic).

**Property:**

Concurrent writes to same session: (1) both succeed (no 409), (2) final state is last-write-wins (full replacement, not merge), (3) no partial updates, (4) client not required to handle optimistic-locking errors.

**Implies:**
- Concurrency strategy: last-write-wins via full replacement or version-based conflict resolution — flag for Tweedledum.
- Idempotency: repeated identical PATCH is idempotent (no double-apply) — flag for contract.
- Testing: test at 2-concurrent-writes level minimum — flag for test harness.
