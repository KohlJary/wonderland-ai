## Test Scenario 004: Break pause/resume state machine — completion cannot fire while paused

**Severity:** degradation

**Setup:**

A break session is running (status='running'). Keisha pauses it (status='paused'). Due to a scheduler glitch, timer event, or test artifact, a completion signal still arrives.

**Trigger:**

While break.status='paused', the backend receives a completion POST or internal event with the session's elapsed time at or past the configured duration.

**Expected:**

The backend should:
- EITHER reject the completion with 409 Conflict ("session is not in a completable state")
- OR accept the completion but leave the session status='paused' (no state transition)

The session should NOT auto-transition to status='completed' while paused.

**Concern:**

Paused sessions are a special state. The user explicitly paused; they did not consent to automatic completion. If a completion fires anyway, the timer might notify Keisha while the session is paused on her screen, or the UI and backend might diverge (frontend sees paused, backend sees completed).

This tests the state machine's discipline: can you transition from 'paused' to 'completed' directly, or only 'paused' -> 'running' -> 'completed'?

**Property:**

For any session S with status='paused':
- A completion event on S does not transition S to status='completed'
- S either remains='paused' (no-op) or transitions to an error state (conflict)
- The session's remaining_seconds and elapsed_seconds do not change due to the completion attempt

Corollary: A paused session can only be advanced by an explicit resume action.

**Implies:**

This tests the backend's state machine discipline. Caterpillar should review the session status-transition logic to ensure that pause is a "hard stop" — no side effects, no automatic unwinding. If pause/resume are implemented as flags or counters rather than state, this test will catch the bug.

Also: Dormouse should watch for production cases where this boundary is crossed. If users report sessions silently completing while paused, the state machine logic is the first place to look.
