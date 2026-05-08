## Scenario 003: Timer fires while session is paused (state collision)

**Severity:** silent-wrongness

**Setup:**

A focus session is running. Marcus worked ~24 minutes and taps Pause. Session is status='paused' with 1 minute remaining.

**Trigger:**

The completion event fires while the session is paused (scheduler glitch or test artifact).

**Expected:**

Session remains status='paused'. No notification fires. Marcus can resume or dismiss explicitly.

**Concern:**

If timer fires while paused, backend might mark session 'completed' even though Marcus is working (just paused). Notification fires unexpectedly. State machine must guard this.

**Property:**

Session state machine rejects invalid transitions. 'paused' → 'completed' only via explicit user action or resume-then-completion.

**Implies:**
- Requires state-transition guards in session model — **contract-001 must define valid transitions.**
- Completion handler must check status before accepting completion.
