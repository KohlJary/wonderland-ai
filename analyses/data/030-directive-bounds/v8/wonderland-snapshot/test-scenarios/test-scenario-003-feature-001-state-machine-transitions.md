## Test Scenario 003: State machine transitions enforced (Feature 001)

**Feature:** Run a focus session with breaks
**Severity:** high

**Scenario:**

The backend enforces the session state machine: running ↔ paused → completed (one-way). A client attempts invalid transitions:
1. Call /api/sessions/current/pause when state is already paused
2. Call /api/sessions/current/complete when state is still running (not fired yet)
3. Call /api/sessions/{id}/resume after session is completed

The backend rejects all three with appropriate error states.

**What breaks if this fails:**

The session state can become incoherent (paused and completed simultaneously), leading to data that the history view cannot interpret, or clients stuck waiting for a transition that will never happen.

**Acceptance Criteria:**

- pause() when already paused: 409 Conflict with message "session is already paused"
- complete() when state is still running: 409 Conflict with message "session must reach timer expiry before completion"
- resume() on completed session: 409 Conflict with message "cannot resume a completed session"
- All invalid-transition errors include current state in response for debugging
