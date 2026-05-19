## Scenario 190: Kohl types 'experiment' and sees matching notes within 200ms

**GUID:** 01KRXYDGJMBMVN3X0NM5ETQ1NS
**Severity:** degradation

**Setup:**

Kohl has 12 notes: 8 with 'experiment' in title or body, 4 without. She is on the search page with an empty query input.

**Trigger:**

Kohl types 'experiment' into the search box (300ms debounce fires after she pauses typing).

**Expected:**

Within 200ms of the debounce firing, the results list shows exactly 8 notes. Each matching note highlights the word 'experiment' in its title or body preview. The result count reads '8 results'.

**Concern:**

If search latency exceeds 200ms, Kohl perceives the app as sluggish and may lose confidence in the search feature. Real-time search requires snappy feedback.

**Property:**

search response time must be ≤200ms for ≤1000 notes

**Implies:**
- backend-search-endpoint-must-use-indexed-full-text-search-not-sequential-scan
- frontend-must-debounce-to-avoid-thrashing-backend-with-every-keystroke
