## Test Scenario: Session Abandonment Idempotency and State Transitions

**Severity:** breakage, degradation

**Setup:**

Jordan wants to abandon an active session. She taps the abandon button. The button might be tapped twice (double-tap, network retry) or she might try to abandon a session that's already completed or already deleted. The system must handle these state transitions correctly and idempotently.

**Trigger:**

Jordan performs these actions:
1. Start session A (active)
2. DELETE /sessions/{A.id} (abandon)
3. DELETE /sessions/{A.id} again (network retry or double-tap)
4. Start session B and complete it
5. Try DELETE /sessions/{B.id} (try to abandon completed session)
6. Try DELETE /sessions/9999 (nonexistent session)

**Expected:**

1. Start returns 201 Created with active session
2. First DELETE returns 200 OK or 204 No Content; session is marked deleted
3. Second DELETE returns idempotent response:
   - Either 204 No Content (soft delete already applied, no error)
   - Or 404 Not Found (session is gone; client knows it's already deleted)
   - NOT 200 OK with success message (misleading; nothing changed)
4. Completed session DELETE returns 409 Conflict or 403 Forbidden (can't abandon completed work)
5. Nonexistent session DELETE returns 404 Not Found

**Concern:**

Breakage:
- Completed session is deleted when user thinks they're abandoning active session (wrong state machine)
- DELETE is not idempotent; second DELETE returns 200 with no indication something's already deleted
- Abandoned session still appears in today's count (soft delete not implemented)

Degradation:
- DELETE /sessions/{A.id} returns 500 error instead of clear 4xx
- Attempting to DELETE completed session returns 200 (silently accepted) instead of 409 (conflict)
- No error message distinguishing "session doesn't exist" from "session is already deleted"
- Frontend shows "abandon" button for completed sessions, inviting wrong action

Silent-wrongness:
- DELETE succeeds (200) but abandoned session still appears in GET /sessions/today
- Abandoned then re-created session with same ID causes confusion (IDs should be unique + never reused)

**Property:**

For all users U and sessions S:
- S is in state: ACTIVE, COMPLETED, or DELETED
- DELETE /sessions/{S.id} is only valid when S.state = ACTIVE
- DELETE returns idempotent response (200, 204, or 404, never 200 with success message on retry)
- After DELETE, GET /sessions/today does not include S
- DELETE /sessions/{S.id} followed by POST /sessions/start returns new session with different ID

**Implies:**

- Implies state machine: ACTIVE → COMPLETED or DELETED (not both)
- Implies soft delete (is_deleted flag) or explicit DELETED state (for history preservation)
- Implies filtering on GET endpoints to exclude DELETED sessions
- Implies clear HTTP status codes: 409 for state conflict, 404 for not found, 204 for idempotent success
