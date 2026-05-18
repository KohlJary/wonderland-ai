## Scenario: 409 Conflict response body includes the current server state so client can decide what to do

**Severity:** degradation

**Setup:**
Note id=1 with revision_id='hash_old'. Client A sends PUT with If-Match: hash_old. Meanwhile, server's note has been updated to revision_id='hash_new' (by Client B or another process).

**Trigger:**
Client A's PUT request arrives at the server. The If-Match validation fails (hash_old != hash_new).

**Expected:**
PUT returns 409 Conflict with response body:
```json
{
  "error": "ConflictError",
  "message": "Note has been modified. Please review the current version.",
  "server_revision_id": "hash_new",
  "server_state": {
    "id": 1,
    "title": "updated title",
    "body": "updated body",
    "tag_ids": [10, 11],
    "tag_names": ["research", "async"],
    "created_at": "2026-05-18T17:13:21Z",
    "updated_at": "2026-05-18T17:14:00Z",
    "revision_id": "hash_new"
  }
}
```
This allows Client A's frontend to display the conflict modal with the current state, letting the user choose to overwrite, merge, or discard their changes.

**Concern:**
If the 409 response body is empty or missing server_state, the frontend cannot show the user what the server has. The user only sees "Conflict!" with no context. This makes the UI non-functional for the multi-tab editing scenario.

**Property:**
For all 409 Conflict responses, the response body includes: error code, server_revision_id, and server_state (full note object with all fields including current revision_id).

**Implies:**
- Implies the PUT endpoint must define a 409 response model (Pydantic schema) that includes server_state.
- Implies server_state must be identical to what GET /notes/{id} would return (so client can trust it as the source of truth).
- Implies revision_id in server_state must be the current hash (hash_new), not the old one.

