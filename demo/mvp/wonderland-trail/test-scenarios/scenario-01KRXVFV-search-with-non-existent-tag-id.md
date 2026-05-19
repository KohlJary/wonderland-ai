## Scenario 080: Search with non-existent tag ID

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9M
**Severity:** degradation

**Setup:**

Database has notes, but tag_id=99999 doesn't exist

**Trigger:**

GET /api/search?query=&tag_ids=99999

**Expected:**

Returns 200 with empty array (no notes have that tag)

**Concern:**

The endpoint might return 404 or 400 (wrong status code) instead of 200. Or it might crash with a database error.

**Property:**

For all invalid tag IDs, search returns 200 with empty array (or valid result, depending on error semantics).
