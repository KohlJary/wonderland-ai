## Scenario 018: Break pause/resume state machine — completion cannot fire while paused

**Severity:** degradation

**Setup:**

Break paused (status='paused'). Due to glitch, completion signal arrives while paused.

**Trigger:**

Backend receives completion POST/event while session.status='paused'.

**Expected:**

Rejects (409) or ignores (200 no-op). Status remains 'paused', not 'completed'.

**Concern:**

Paused sessions are explicit user choice. If completion fires anyway, timer notifies while paused on screen, or UI/backend diverge. Tests state-machine: can you transition paused→completed directly?

**Property:**

For S with status='paused', completion event does not transition S to 'completed'. S remains 'paused' (no-op) or moves to error. remaining_seconds unchanged.

**Implies:**
- Tests state-machine rigor. Caterpillar should review status-transition logic.
- If pause/resume are flags instead of states, this test catches bug.
