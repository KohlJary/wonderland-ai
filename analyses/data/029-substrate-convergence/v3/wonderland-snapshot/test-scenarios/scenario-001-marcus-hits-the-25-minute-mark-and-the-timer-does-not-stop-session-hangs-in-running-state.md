## Scenario 001: Marcus hits the 25-minute mark and the timer does not stop — session hangs in 'running' state

**Severity:** breakage

**Setup:**

Marcus starts a fresh session. The timer begins at 25:00 and counts down. No other sessions are running. The system clock is synchronized.

**Trigger:**

The countdown reaches 00:00 — the session duration has elapsed.

**Expected:**

The timer transitions to 'break' state. The UI shows 'Break: 5:00' and begins counting down. The session is recorded to history.

**Concern:**

State machine transitions are easy to miss — the implementation will count down correctly but forget to emit the completion event or write to history. The session will sit in 'running' state until the user manually stops it or force-quits the app.

**Property:**

For all completed sessions S with duration D, within 500ms of system.now() >= S.started_at + D, the session's state transitions to 'break' AND an immutable entry is written to SessionRecord.

**Implies:**
- Depends on Tweedles' state machine contract (session lifecycle from Feature-001 contract).
- Depends on backend write-to-history atomicity — if the transition fires but the write fails, we have silent wrongness.
