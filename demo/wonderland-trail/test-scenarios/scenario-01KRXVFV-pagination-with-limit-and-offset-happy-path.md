## Scenario 074: Pagination with limit and offset (happy path)

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9E
**Severity:** degradation

**Setup:**

Database contains 100 notes. User requests 10 results per page.

**Trigger:**

GET /api/search?query=note&limit=10&offset=0 (first page), then offset=10 (second page)

**Expected:**

First call returns 10 results; second call returns notes 11-20. Pagination is consistent across pages.

**Concern:**

Pagination logic might have off-by-one errors, or might skip/duplicate results across pages if ordering isn't stable. Or limit/offset might not be implemented at all and the endpoint returns all 100 results.

**Property:**

For all paginated queries P with limit L and offset O, results(P, O) ∩ results(P, O+L) = ∅ (pages are disjoint) and results(P, O) ∪ results(P, O+L) ⊆ results(P, ∞) (paginated results are subsets of full result set).
