## Scenario 007: Rapid-fire DELETE (three retries in 50ms) remains idempotent; no state flip-flops or corrupted invariants

**Severity:** degradation

**Setup:**

Active session. User taps abandon, client retries 2x due to network timeout. Backend receives DELETE /sessions/{id} three times in rapid succession (<50ms).

**Trigger:**

DELETE /sessions/{id}, DELETE /sessions/{id}, DELETE /sessions/{id} — rapid retries.

**Expected:**

First DELETE returns 204. Second and third return 204 (idempotent) or 404 (already deleted). No error. Session marked deleted exactly once. State invariants (is_deleted=true, is_active=false) hold.

**Concern:**

Without idempotency guards, concurrent DELETEs might revert is_deleted flag or create state where both is_deleted and is_active are true (violating model invariants).

**Property:**

DELETE /sessions/{id} is idempotent: DELETE(x) == DELETE(DELETE(x)). Multiple calls return same response code and leave session in same state.

**Implies:**
- Implies backend must use conditional updates: UPDATE sessions SET is_deleted=true WHERE id=? AND is_deleted=false (only update if not already deleted).
- Implies test harness needs concurrency fixtures to trigger rapid sequential calls with minimal delay.
