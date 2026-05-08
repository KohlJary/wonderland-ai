## Scenario 005: Resume tapped while session is already running (invalid transition)

**Severity:** degradation

**Setup:**

Focus session running. Marcus accidentally taps 'Resume' (not paying attention or confusing UI).

**Trigger:**

Resume request fires while status='running'.

**Expected:**

Request rejected (400) or idempotently returns 200 with status='running'. Session not confused or frozen.

**Concern:**

If backend processes resume as valid transition, it might apply side effects twice. If it crashes (500), UI hangs.

**Property:**

State transitions guarded by preconditions. Resume valid only when status='paused'.

**Implies:**
- Requires state-transition guards — **contract-001 must define valid transitions.**
