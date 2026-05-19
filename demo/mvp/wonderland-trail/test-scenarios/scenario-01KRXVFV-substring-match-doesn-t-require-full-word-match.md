## Scenario 072: Substring match doesn't require full word match

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9C
**Severity:** breakage

**Setup:**

Note with title='Searching for truth', body='empty'

**Trigger:**

GET /api/search?query=arch (substring of 'Searching')

**Expected:**

Note is returned in results

**Concern:**

The code might implement word-boundary matching instead of substring matching. Or it might search only on full title, not on content within title.

**Property:**

If substring S is present in a note's title or body, search(S) returns that note.
