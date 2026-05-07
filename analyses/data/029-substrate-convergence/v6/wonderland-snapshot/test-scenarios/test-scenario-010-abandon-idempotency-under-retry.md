## Scenario: Session abandon idempotency under rapid retries; DELETE issued 3x in 50ms, no state corruption

**Severity:** degradation

**Setup:**

Active session with id=42. User's client has a broken network retry mechanism (or flaky network). When the user taps "Abandon," the frontend sends `DELETE /sessions/42` immediately. No response arrives within 30ms, so the client retries. No response again, so the client retries a second time. All three `DELETE` requests hit the backend within 50ms total.

**Trigger:**

`DELETE /sessions/42`, `DELETE /sessions/42` (retry), `DELETE /sessions/42` (retry again) — rapid-fire in <50ms.

**Expected:**

All three requests succeed:
- First `DELETE` returns 204 No Content (or 200 with empty body). Session is marked `is_deleted=true`.
- Second `DELETE` returns 204 or 404 (idempotent — session is already deleted). No error.
- Third `DELETE` returns 204 or 404 (idempotent — session is already deleted). No error.

Session state is marked deleted exactly once. No flip-flops, no corrupted state.

**Concern:**

Without proper idempotency guards, the second or third `DELETE` might:
- Revert the `is_deleted` flag back to false (if update logic doesn't check the current state).
- Cause a race where session state becomes inconsistent (e.g., both `is_deleted=true` and `is_active=true` simultaneously, violating the model invariant).
- Throw a 500 error due to a logic assumption that assumes the first delete succeeded in isolation.

Result: silent wrongness (session state is corrupted) or degradation (error instead of idempotent success).

**Property:**

`DELETE /sessions/{id}` is idempotent: for any session `x`, `DELETE(x)` == `DELETE(DELETE(x))` == `DELETE(DELETE(DELETE(x)))`. The response code and session state are identical regardless of how many times DELETE is called.

**Implies:**

- Implies backend must use conditional updates: `UPDATE sessions SET is_deleted=true WHERE id=? AND is_deleted=false` (only update if not already deleted).
- Implies backend must not rely on order-dependent logic (e.g., "first delete sets flag, second delete reverts it").
- Implies test harness needs ability to trigger rapid-fire requests to the same endpoint. Current conftest uses a synchronous TestClient; concurrency would require threading or asyncio with tight timing.

**Note:** Tweedledee's test file includes `test_abandon_already_abandoned_session_returns_idempotent`, which is a good start. This scenario goes deeper: it tests the state invariants under actual rapid retries, not just sequential calls.
