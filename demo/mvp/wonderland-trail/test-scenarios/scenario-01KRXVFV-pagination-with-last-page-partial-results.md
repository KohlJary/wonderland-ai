## Scenario 084: Pagination with last page partial results

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9R
**Severity:** curiosity

**Setup:**

Database has 25 notes matching query. Requesting with limit=10.

**Trigger:**

GET /api/search?query=test&limit=10&offset=20 (third page, which is partial)

**Expected:**

Returns 5 notes (the remaining notes), not an error or empty array

**Concern:**

The endpoint might return 404 when offset exceeds result count, or might return empty array without indicating that it's the last page.

**Property:**

For all offsets O within the result set size, search returns the remaining results (possibly fewer than limit).
