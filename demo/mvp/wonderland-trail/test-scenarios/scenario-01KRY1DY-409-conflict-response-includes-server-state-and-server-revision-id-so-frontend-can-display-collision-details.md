## Scenario 352: 409 Conflict response includes server_state and server_revision_id so frontend can display collision details

**GUID:** 01KRY1DY1PSMHZM094C8W7E46S
**Severity:** degradation

**Setup:**

Client A sends PUT with stale If-Match. Server detects collision.

**Trigger:**

Server returns 409 Conflict.

**Expected:**

Response body includes: {error: 'ConflictError', server_revision_id: 'current_hash', server_state: {id, title, body, tag_ids, tag_names, created_at, updated_at, revision_id}}. Frontend can display the collision modal with server's current state.

**Concern:**

If 409 response is empty or missing server_state, frontend cannot show the user what the server has. UI is broken for multi-tab editing.

**Property:**

For all 409 Conflict responses, the response body includes error, server_revision_id, and server_state (full note object).

**Implies:**
- Implies PUT endpoint has a dedicated 409 response model (Pydantic).
