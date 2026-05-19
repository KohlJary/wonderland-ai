## Scenario 078: Text search AND tag filter together

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9J
**Severity:** breakage

**Setup:**

Note A: title='research', tags=['work']. Note B: title='research', tags=['personal']. Note C: title='cooking', tags=['work'].

**Trigger:**

GET /api/search?query=research&tag_ids=<work-id> (search for 'research' AND has 'work' tag)

**Expected:**

Returns only note A (matches text AND has tag)

**Concern:**

The code might OR the conditions (return A, B, C) or ignore one of them entirely. Or it might have the semantics backwards.

**Property:**

For all queries Q and tag sets T, search(Q, T) returns notes that match Q AND have at least one tag in T.
