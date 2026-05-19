## Scenario 335: 409 Conflict response includes full server state so client can show collision UI

**GUID:** 01KRY1DJHRX8TH9EM6XEXWJ9BC
**Severity:** degradation

**Setup:**

Tab B receives 409 Conflict response after attempting a save with stale If-Match.

**Trigger:**

Frontend parses the 409 response body.

**Expected:**

Response body is valid JSON: {error: 'ConflictError', server_revision_id: string, server_state: {id, title, body, tag_ids, tag_names, updated_at, created_at, revision_id}}. All fields present and non-null (empty arrays for tags if none).

**Concern:**

If 409 response is missing server_state or includes only partial state (no tag_ids, no body), frontend cannot show full conflicting version. User cannot make informed choice. If tag_ids is missing, user loses tag associations when accepting server version.

**Property:**

For all 409 Conflict responses, response body includes complete current view of the note on server. Schema matches successful GET response including revision_id.
