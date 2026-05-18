## Scenario 273: Response body on 409 Conflict includes the server's current revision_id so the client knows what the new state hash is

**GUID:** 01KRY19VMP015JW631HNJ74GC7
**Severity:** breakage

**Setup:**

Collision detected: client's If-Match doesn't match server's current revision_id.

**Trigger:**

PUT /notes/1 with If-Match: <stale_revision> and new edits. Server detects collision.

**Expected:**

Response is 409 Conflict with body {error: 'ConflictError', server_revision_id: 'sha256_abc...', server_state: {id, title, body, tag_ids, tag_names, created_at, updated_at}}. The client reads server_revision_id and uses it if the user chooses 'load backend version'.

**Concern:**

If the 409 response doesn't include revision_id, the frontend can't update its local revision_id cache after the collision. The user would be stuck in a collision-loop: each retry would have the same (now-stale) revision_id and keep failing.

**Property:**

For all 409 Conflict responses from PUT /notes/{id}, the response body includes (server_revision_id, server_state). The server_state is the complete current note (id, title, body, tag_names, tag_ids, created_at, updated_at).

**Implies:**
- Requires 409 response schema specification in the contract — flag for Tweedledum.
- Requires test coverage that verifies 409 response shape.
