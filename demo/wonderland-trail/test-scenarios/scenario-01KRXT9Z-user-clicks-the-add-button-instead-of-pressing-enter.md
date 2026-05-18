## Scenario 023: User clicks the 'Add' button instead of pressing Enter

**GUID:** 01KRXT9ZVW04FW51CD98MPDCEZ
**Severity:** breakage

**Setup:**

TagInput component with text input containing 'python' and an 'Add' button beside it.

**Trigger:**

User clicks the Add button.

**Expected:**

Tag 'python' is added to the chip list, input is cleared, input is re-focused.

**Concern:**

Button click handler might not be wired, or might not clear the input afterward.
