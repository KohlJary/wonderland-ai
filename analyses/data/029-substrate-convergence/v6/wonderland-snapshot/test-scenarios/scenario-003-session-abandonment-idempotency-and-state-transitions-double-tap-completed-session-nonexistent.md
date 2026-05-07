## Scenario 003: Session abandonment idempotency and state transitions — double-tap, completed session, nonexistent

**Severity:** degradation

**Setup:**

Jordan abandons active session, then taps abandon twice (network retry). She tries to abandon a completed session and nonexistent session ID.

**Trigger:**

DELETE /sessions/{active_id}, then DELETE /sessions/{active_id} again. DELETE /sessions/{completed_id}. DELETE /sessions/9999.

**Expected:**

First DELETE returns 200/204. Second DELETE returns 204 or 404 (idempotent), never 200 OK. Completed session DELETE returns 409 or 403. Nonexistent returns 404. Abandoned session absent from GET /sessions/today.

**Concern:**

Completed session deleted when trying to abandon (state machine broken, data loss). DELETE not idempotent: second DELETE returns 200, misleading client. Abandoned session still counts in today's summary (soft delete failed). Completed session DELETE returns 200 (silently accepted) instead of 409.

**Property:**

States: ACTIVE, COMPLETED, DELETED. DELETE valid only when state=ACTIVE. DELETE idempotent: never 200 on retry. After DELETE, GET /sessions/today excludes S. Second DELETE returns 204 or 404.

**Implies:**
- Implies state machine: ACTIVE → COMPLETED or DELETED (mutually exclusive)
- Implies soft delete (is_deleted flag) for history preservation
- Implies filtering on all GET endpoints to exclude DELETED sessions
- Implies idempotent DELETE: 204 or 404 on retry, never 200 with success message
