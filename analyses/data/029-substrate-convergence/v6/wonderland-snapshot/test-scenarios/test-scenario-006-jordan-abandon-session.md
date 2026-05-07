## Test Scenario: Jordan Abandons a Session Without Affecting History

**Severity:** degradation (if this fails, Jordan's history is cluttered with interruptions)

**Setup:**

Jordan is a 29-year-old consultant who gets interrupted by meetings. She's 10 minutes into a 25-minute focus session when a calendar alert pops. She needs to stop the timer and attend the meeting. Her history should reflect only completed, meaningful work blocks.

**Trigger:**

Jordan taps the "Abandon Session" button during the active timer. A confirmation appears: "This session will not be saved." She confirms. The session disappears from the timer screen.

**Expected:**

1. During an active session, there is an "Abandon Session" button (UI confirmation)
2. DELETE /sessions/{id} returns HTTP 200 or 204 (success)
3. The abandoned session no longer appears in GET /sessions/today
4. The count in today's summary remains unchanged (or decreases if the session was there temporarily)
5. Jordan can immediately start a new session with POST /sessions/start
6. Subsequent GET /sessions/history does not include the abandoned session
7. Completed sessions before and after the abandon are unaffected

**Concern:**

The concern is that:
- The abandon button might be hard to find (UX issue, but backend confirms the semantics)
- A second tap (network retry) might fail with 404 instead of 409 (idempotency concern)
- Completed sessions might be accidentally deleted if the state machine is confused
- The abandoned session might still appear in history (soft delete not implemented)
- User might want to undo an abandon (not in v1, but should be noted for future)

**Property:**

For all users U and sessions S:
- If S is abandoned via DELETE /sessions/{S.id}, then S does not appear in GET /sessions/today
- DELETE is idempotent: second DELETE returns 404 or 409, not 200
- Completed sessions are not affected by DELETE of another session
- POST /sessions/start succeeds immediately after DELETE

**Implies:**

- Implies DELETE /sessions/{id} endpoint
- Implies soft delete (is_deleted flag) or hard delete (complete removal)
- Implies state-machine check: only active sessions can be deleted (not completed)
- Implies filtering: GET /sessions/today and GET /sessions/history exclude deleted sessions
