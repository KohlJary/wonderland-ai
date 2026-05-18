## Scenario 076: Tag filtering with valid tag IDs

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9G
**Severity:** breakage

**Setup:**

Three notes: note A tagged 'work', note B tagged 'personal', note C tagged both 'work' and 'personal'.

**Trigger:**

GET /api/search?query=&tag_ids=<work-tag-id> (search for all notes with 'work' tag, no text query)

**Expected:**

Returns notes A and C (both have 'work' tag), excludes B

**Concern:**

Tag filtering might not work at all (ignores tag parameter), or might require a text query to be present, or might AND all tags instead of OR-ing them.

**Property:**

For all notes N and tag ID T, search with tag_ids=[T] returns all and only notes tagged with T.
