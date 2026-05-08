## Scenario 012: Break timer can be skipped (user taps 'Skip Break', goes straight to next focus)

**Severity:** degradation

**Setup:**

Break timer is running. User has not yet skipped.

**Trigger:**

User taps 'Skip Break' button. A skip event is emitted. The app transitions to a new focus session (or idle state waiting for next focus).

**Expected:**

Break session is marked as 'skipped' (not 'completed'). No audio notification. UI shows focus mode (or idle) immediately. Daily history records the break as skipped (not part of total break time).

**Concern:**

Keisha's story says 'skip the break and go straight to the next focus session.' But the contracts don't mention a skip action. Does the skip flow through the same session-completion event (with status='skipped'), or a different endpoint? If it's not in the contract, M5 might not implement it, and the feature will be incomplete.

**Property:**

When a break session is skipped, its status should be 'skipped', not 'completed' or 'running'. It should not appear in daily break-time totals.

**Implies:**
- This scenario might expose a contract gap. Tweedledum: does Contract-001 or Contract-003 define a 'skip' action? If not, Keisha's acceptance criterion ('skip the break and go straight to the next focus session') is at risk.
- If skip is in-scope, it should be a PATCH /sessions/{id} { action: 'skip' } or a POST /sessions/{id}/skip, with idempotency.
