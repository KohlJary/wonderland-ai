## Scenario 004: Pause button tapped three times rapidly (idempotency)

**Severity:** degradation

**Setup:**

Focus session running. Marcus nervously taps pause three times in rapid succession.

**Trigger:**

Three pause requests fire within 100ms.

**Expected:**

First pause succeeds (status='paused'). Second and third return idempotent responses (no error, no state change). Session remains functional.

**Concern:**

Without idempotency checks, backend gets confused or client sees state oscillations. Second pause might error and freeze the UI.

**Property:**

Pause action is idempotent — multiple identical requests have same effect as one.

**Implies:**
- Requires idempotency guards on state transitions.
