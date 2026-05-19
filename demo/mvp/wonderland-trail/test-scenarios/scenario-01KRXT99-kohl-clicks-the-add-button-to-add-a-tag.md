## Scenario 011: Kohl clicks the Add button to add a tag

**GUID:** 01KRXT99M7QSR234FW4T0095TR
**Severity:** breakage

**Setup:**

The editor is open. TagInput shows a text input with the text 'results-batch-2' and an 'Add' button next to it.

**Trigger:**

Kohl clicks the Add button.

**Expected:**

The tag 'results-batch-2' appears as a chip below the input. The input clears. The focus returns to the input field (or stays there, allowing rapid tag entry).

**Concern:**

If the Add button is non-functional or the tag doesn't appear, mouse-driven users are blocked from adding tags.

**Property:**

Tag addition via click button works as expected
