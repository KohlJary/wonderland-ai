## Scenario 009: Break timer auto-starts when focus session completes

**Severity:** breakage

**Setup:**

A focus session is running and about to complete. Session has type='focus', elapsed_ms approaches duration_seconds * 1000.

**Trigger:**

Focus session reaches completion (elapsed_ms >= duration_seconds * 1000).

**Expected:**

System automatically transitions to a new session with type='break', status='running', elapsed_ms=0, without user interaction. Break session appears in session state immediately.

**Concern:**

Auto-start is mentioned in the contract but the trigger and state transition are not precisely defined. Does the focus session completion endpoint return the new break session? Or must client poll? The ambiguity is the seam.

**Property:**

For every completed focus session, a break session with type='break' must exist in the same transaction or immediately after completion.

**Implies:**
- Implies contract clarification: does focus completion return the break session object, or does client fetch separately?
- Implies frontend contract detail: what triggers auto-transition in UI after focus completes?
