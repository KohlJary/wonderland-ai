## Scenario 177: Kohl searches for an empty string and sees her whole archive

**GUID:** 01KRXY92H4EWNSQ2AXJ0WRT1FG
**Severity:** degradation

**Setup:**

Kohl wants to browse all her notes without a filter — maybe she's looking for something but doesn't know the word. She taps the search box and presses enter without typing anything.

**Trigger:**

Empty search query submitted.

**Expected:**

The full list of her notes appears in the same view, in a sensible order (most recent first, or by creation order — consistent with how they appear elsewhere).

**Concern:**

If empty search throws an error or returns nothing, Kohl will think the search feature is broken, or that she somehow deleted all her notes. Degradation: the feature *appears* to work but fails in a basic case.

**Property:**

Edge cases in search queries should be graceful, not error states.
