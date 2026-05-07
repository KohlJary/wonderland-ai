## Test Scenario 014: Break transition is explicit; session cannot be restarted during break

**Severity:** breakage

**Feature:** Feature 001: Run a focused work session with built-in break

**Setup:**

Marcus has completed a 25-minute focus session. The SessionRecord for the session has been written to the DB. The Session record has status=completed. The frontend displays the break countdown (5 minutes, based on settings).

**Trigger:**

Marcus can now either:
a) Wait for the break to auto-complete, or
b) Tap "Skip Break" to start a new session immediately

Marcus taps "Skip Break" to start a new session immediately.

**Expected:**

- The previous Session (the one that's complete) remains in the DB with status=completed.
- A new Session record is created with status=idle (or running, depending on implementation choice).
- The user can now start a new focus session.
- When the new session completes, a new SessionRecord is written (distinct from the previous one).

If Marcus had instead waited for the break to auto-complete, the Session would transition from completed to idle, and he'd be prompted to start a new session.

**Concern:**

If the break is not explicit (i.e., the backend automatically creates a new Session for the break without the frontend requesting it), then:
1. The break might complete without the user noticing, and the app might auto-start a new focus session without their intent.
2. If the user closes the app during the break, the app might re-open in a confusing state (is a session running or not?).
3. Multi-device sync will be confusing (which device controls the break state?).

Also, if the backend allows starting a new session while a break Session is still running, the state machine is broken.

**Property:**

For all session completions, a new break Session must be explicitly created (via POST /api/session/start-break or similar) before a new focus Session can be created. Break transitions are not implicit.

**Implies:**

This tests the explicit break session model in Feature 001. The contract specifies "break as explicit new session." This scenario validates that the implementation honors the contract.

