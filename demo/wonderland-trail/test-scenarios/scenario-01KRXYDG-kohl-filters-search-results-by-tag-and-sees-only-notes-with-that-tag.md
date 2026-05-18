## Scenario 192: Kohl filters search results by tag and sees only notes with that tag

**GUID:** 01KRXYDGJMBMVN3X0NM5ETQ1NV
**Severity:** silent-wrongness

**Setup:**

Kohl has 5 notes tagged 'research', 3 tagged 'meeting', and 2 untagged. She searches for 'note' (which matches all 10) and the results page shows all 10 notes.

**Trigger:**

Kohl clicks the 'research' tag filter button. The filter state updates to show only notes with the 'research' tag.

**Expected:**

The results list now shows exactly 5 notes (all tagged 'research'). The result count reads '5 results'. The 'research' tag filter button appears selected/highlighted.

**Concern:**

If the filter doesn't apply, Kohl sees all 10 notes and may not notice the filter is broken. The feature claim is 'optional secondary filtering' — if it silently doesn't work, the feature is incomplete.

**Property:**

tag-filter-must-correctly-reduce-result-set-using-AND-semantics
