## Scenario: 409 Conflict response includes full server state so client can show collision UI

**Severity:** degradation

**Setup:**

Tab A and Tab B collide on save (per scenario 01KRY1AB):
- Tab B receives 409 Conflict response from the server.

**Trigger:**

Frontend parses the 409 response body.

**Expected:**

Response body is valid JSON with complete note schema:

```json
{
  "error": "ConflictError",
  "server_revision_id": "hash_new",
  "server_state": {
    "id": 42,
    "title": "New Title",
    "body": "...",
    "tag_ids": [1, 3],
    "tag_names": ["async", "rust"],
    "created_at": "2025-01-17T10:00:00Z",
    "updated_at": "2025-01-18T14:31:00Z",
    "revision_id": "hash_new"
  }
}
```

All fields are present and non-null (except tag_ids and tag_names are empty arrays if the note has no tags).

**Concern:**

If the 409 response is missing server_state, or includes only a partial state (e.g., no tag_ids, no body, no updated_at), the frontend cannot show Kohl the full conflicting version. She cannot make an informed choice between "Keep My Edits" and "Accept Server Version."

Worst case: if tag_ids is omitted, Kohl accepts the server version and loses all tag associations without realizing it (silent data loss).

This becomes a degradation rather than breakage because the app still works (409 is returned, collision is detected), but the user cannot resolve it with full information.

**Property:**

For all 409 Conflict responses, the response body includes server_state with complete current view of the note on the server. The schema of server_state must match the successful GET /api/notes/{id} response schema.

**Implies:**

Implies API contract: document the 409 response schema. Frontend developers need to know what fields to expect in order to render the collision UI.

Implies code: the endpoint must return the current, live note state (not cached, not partial) in the 409 response.
