## Scenario 232: Kohl searches a query with no matches and expects an empty result list

**GUID:** 01KRXYFQH721FMRYBB1WJJ1A0J
**Severity:** degradation

**Setup:**

Kohl has created several notes with various content. She opens search.

**Trigger:**

Kohl types 'xyzabc' (a string that appears in none of her notes).

**Expected:**

The search results show 'No notes found' or an empty list. The result count shows 0. Kohl sees a message like 'No results for xyzabc' to confirm the search ran and found nothing (not that it failed).

**Concern:**

If the search returns an error instead of empty results, Kohl thinks the feature is broken. If results silently show old results from a prior search, Kohl is confused.

**Property:**

No-match queries return an empty result set with a clear message indicating the search completed successfully but found nothing.
