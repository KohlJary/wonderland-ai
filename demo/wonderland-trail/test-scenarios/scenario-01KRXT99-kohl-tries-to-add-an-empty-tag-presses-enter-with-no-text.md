## Scenario 016: Kohl tries to add an empty tag (presses Enter with no text)

**GUID:** 01KRXT99M7QSR234FW4T0095TX
**Severity:** degradation

**Setup:**

The TagInput is focused and empty. Kohl presses Enter.

**Trigger:**

Enter is pressed with zero characters in the input.

**Expected:**

Nothing happens. No chip is added. The input remains empty and focused. No error is shown (this is a normal non-action, not an error state).

**Concern:**

If an empty tag is added as a chip, or if an error message appears, Kohl's experience is degraded. Empty tags are meaningless and clutter the list.

**Property:**

Empty tag input is rejected silently
