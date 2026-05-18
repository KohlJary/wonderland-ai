## Scenario 082: Results ordered by relevance or recency

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9P
**Severity:** curiosity

**Setup:**

Multiple notes matching the query, with different recency and match quality

**Trigger:**

GET /api/search?query=test (multiple matches)

**Expected:**

Results are consistently ordered (either by match quality, by recency, or by ID — any consistent order)

**Concern:**

Results might be in random order, or order might change between requests, making pagination unreliable.

**Property:**

For all identical queries Q issued twice, the ordering of results is identical (deterministic).
