## Scenario 087: Kohl filters results to only notes tagged 'performance' when she has 50 notes total

**GUID:** 01KRXVGHT2Y73C5JV7SEK1JJ75
**Severity:** degradation

**Setup:**

Kohl has written 50 notes. 12 are tagged 'performance'. She's looking for a specific benchmark result and wants to narrow the list.

**Trigger:**

Kohl types 'latency' in the search box, selects the 'performance' tag from the filter dropdown, and waits for results.

**Expected:**

Results show only notes matching both 'latency' substring AND tagged 'performance'. If there are 3 matches, she sees page 1 of 1 with 3 results. Pagination metadata shows total: 3.

**Concern:**

If tag filtering doesn't work (shows all notes matching 'latency' regardless of tag), or if it uses OR semantics instead of AND, Kohl sees noise. Tag filtering is about focus; broken filtering wastes her time sifting through irrelevant notes.

**Property:**

Tag filter combines with text search using AND logic
