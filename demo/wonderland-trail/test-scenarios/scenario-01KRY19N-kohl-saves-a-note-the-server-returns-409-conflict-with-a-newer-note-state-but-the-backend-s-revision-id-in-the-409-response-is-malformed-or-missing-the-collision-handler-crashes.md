## Scenario 262: Kohl saves a note, the server returns 409 Conflict with a newer note state, but the backend's revision_id in the 409 response is malformed or missing—the collision handler crashes

**GUID:** 01KRY19NJ0GS53FVHNDWBCBT8D
**Severity:** breakage

**Setup:**

Kohl's editor has revision_id 'rev_5' in component state. She clicks Save. Another tab has already modified the note, so the server is at revision_id 'rev_6'.

**Trigger:**

The server responds with 409 Conflict. However, the response body is malformed: it's missing the 'revision_id' field or contains a non-string value (e.g., revision_id: null or an object instead of a string).

**Expected:**

The frontend's collision handler should gracefully degrade. It should either (a) show an error message to Kohl ('Unable to resolve collision; please reload the page'), or (b) automatically reload the page to fetch the latest state from the server. The editor should not crash or enter an infinite loop.

**Concern:**

If the collision handler assumes revision_id is always a string and tries to use it without checking, it could crash the component. If it silently ignores the missing field, it might allow Kohl to proceed with a stale revision_id, which would result in another 409 on the next save.

**Property:**

For all 409 Conflict responses, the frontend must validate the response schema before processing it. If the schema is invalid, the frontend must degrade gracefully (error message + reload suggestion, not crash).

**Implies:**
- Implies validation of the collision response schema before displaying it to Kohl.
