## Scenario 079: Empty query string with tag filter (tag-only search)

**GUID:** 01KRXVFVVKFY5G1VXV7J44PM9K
**Severity:** breakage

**Setup:**

Notes tagged 'work' and 'personal'

**Trigger:**

GET /api/search?query=&tag_ids=<work-id> (empty query, just tags)

**Expected:**

Returns all notes with 'work' tag (query='' is treated as 'match everything' or 'ignore query')

**Concern:**

Empty query might cause SQL errors, or might be treated as 'match nothing' instead of 'match everything'.

**Property:**

For all tag filters T, search(query='', tag_ids=T) returns all notes tagged with at least one tag in T.
