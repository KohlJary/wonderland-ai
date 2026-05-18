## Scenario 178: Kohl searches for a phrase with punctuation and special characters

**GUID:** 01KRXY92H4EWNSQ2AXJ0WRT1FH
**Severity:** silent-wrongness

**Setup:**

Kohl has a note titled 'Cost: $12.50 — should I buy more?' She's trying to remember the note about this expense decision.

**Trigger:**

Kohl searches for 'Cost: $12.50' (the exact phrase from the title).

**Expected:**

The note appears in the results. Kohl sees it and clicks it.

**Concern:**

If the search implementation strips or mishandles special characters, the search will fail silently — Kohl will think she misremembered the title, when actually the search just didn't handle punctuation. If she searches for 'cost 12.50' (without punctuation) and that works, she's learned to search without punctuation, which is a UX friction she shouldn't have to learn.

**Property:**

Search should be forgiving of punctuation and special characters without requiring the user to learn escaping rules.
