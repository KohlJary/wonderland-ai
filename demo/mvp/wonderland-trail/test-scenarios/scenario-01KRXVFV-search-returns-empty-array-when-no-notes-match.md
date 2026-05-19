## Scenario 070: Search returns empty array when no notes match

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9A
**Severity:** degradation

**Setup:**

Database contains notes with title 'Alice' and 'Bob', body 'research' and 'experiment'.

**Trigger:**

GET /api/search?query=xyz (text that doesn't match any note)

**Expected:**

Returns 200 with empty array []

**Concern:**

The endpoint might return 404 or 400 (wrong status code) instead of 200 with []. Or it might crash on the empty-result path if pagination logic isn't defensive.

**Property:**

For all queries Q and all note collections N, search(Q, N) returns 200 with a list (possibly empty) and status 200.
