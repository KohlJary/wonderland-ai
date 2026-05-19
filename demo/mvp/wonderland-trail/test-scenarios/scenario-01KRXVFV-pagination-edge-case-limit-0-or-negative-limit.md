## Scenario 075: Pagination edge case: limit=0 or negative limit

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9F
**Severity:** curiosity

**Setup:**

Database has notes.

**Trigger:**

GET /api/search?query=test&limit=0

**Expected:**

Either rejects (400 Bad Request) or returns empty array. Definitely doesn't return all notes or crash.

**Concern:**

Unvalidated limit parameter might cause SQL errors or return unexpected results.

**Property:**

For all invalid limits L (≤ 0), search with limit=L either rejects the request or returns predictable empty/safe result.
