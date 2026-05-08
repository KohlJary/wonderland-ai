## Scenario 011: Completed break timer does not auto-start next focus session

**Severity:** breakage

**Setup:**

A break timer is running and reaches completion (elapsed_ms >= duration_seconds * 1000). Break session has type='break'.

**Trigger:**

Break timer reaches zero elapsed time (timeout).

**Expected:**

Break session transitions to status='completed', completion_type='timeout'. System does NOT auto-start a new focus session. User must manually tap 'start new session' button.

**Concern:**

The story says next focus must be manual, but the contract doesn't explicitly forbid auto-start. If this is missed, the flow becomes: focus -> break -> focus -> break ad infinitum without user consent.

**Property:**

Break session completion never triggers focus session auto-start.
