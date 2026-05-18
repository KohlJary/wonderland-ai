## Scenario 363: Kohl saves a note with 5 tags; revision_id includes all tag IDs in sorted order

**GUID:** 01KRY1F5JJWC63TXB9SQCCBZWJ
**Severity:** silent-wrongness

**Setup:**

Kohl has typed a title and body, and added 5 tags: {id: 7, name: 'analysis'}, {id: 2, name: 'dataset'}, {id: 9, name: 'research'}, {id: 4, name: 'q4-findings'}, {id: 1, name: 'automation'}. She clicks Save. The POST request body includes tag_ids: [7, 2, 9, 4, 1] (the order they were added by Kohl).

**Trigger:**

The backend receives the POST, persists the note with tags, and computes revision_id. The computation is SHA256(sorted([title, body, sorted_tag_ids, updated_at])). The sorted_tag_ids are [1, 2, 4, 7, 9] (sorted ascending by ID, NOT insertion order).

**Expected:**

The response includes revision_id='xyz789'. On page reload, Kohl loads GET /api/notes/{id}. The response returns the same tags in some order (possibly the insertion order from the request, or possibly sorted). The client computes the revision_id using the same hash algorithm as the server (tag_ids sorted ascending). The computed revision_id matches 'xyz789'. If Kohl opens the note in a second tab (which loads the same note and computes the same revision_id), both tabs have the same revision_id and If-Match validation will not trigger a collision on the next save.

**Concern:**

If revision_id computation doesn't sort tag_ids consistently, two tabs that load the same note might compute different revision_ids (if tag order differs between tabs), leading to false collision warnings or silent overwrites. Silent wrongness because both tabs might believe they're in sync when they're not.

**Property:**

revision_id hash includes tag_ids sorted consistently (ascending by ID)
