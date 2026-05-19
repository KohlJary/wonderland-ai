## Contract Note 021: Revision ID computation and collision detection contract (backend-side)

**GUID:** 01KRY0B83ZTJH7A3D385T0MRGF
**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

Existing POST /api/notes and PUT /api/notes/{id} endpoints do NOT return revision_id, do NOT validate If-Match header, and do NOT handle 409 Conflict scenarios.

**Proposed Change:**

Every note response (POST create, PUT update, GET read) includes revision_id field: opaque string computed as SHA256(sorted([title, body, sorted_tag_ids, updated_at])). Client caches revision_id after successful save. On PUT, client sends If-Match: <cached_revision_id> header. Backend compares: if match, update succeeds (200); if mismatch, return 409 with {error: 'ConflictError', server_revision_id, server_state: full note}. This prevents silent overwrites when multiple tabs save concurrently. Audit trail logs the revision_id with every saved state for forensic clarity.

**Source:** ADR-01KRXWWA (server-authoritative persistence with collision detection, mandatory per Queen ruling-004) + contract-notes 01KRXXCX-multi-tab-collision-detection-revision-id-versioning

**Frontend Impact (Tweedledee):**

Client-side state: (1) After each successful save (200 response), the editor stores the returned revision_id in React state (revisionId state variable). (2) On app boot (useEffect in App component), GET /notes is called; each note's revision_id is stored in the notes array in state. (3) When Save button is clicked, the current revisionId is sent as If-Match header in the PUT request. (4) On 409 Conflict: a modal appears ('Collision Detected') with backend's newer state; user chooses 'Keep my edits' (ignore and retry) or 'Load backend version' (overwrite local edits, update revisionId from conflict response). (5) localStorage keystroke buffer is NOT cleared after successful save; user continues editing. On conflict, if user chooses 'load backend version', the editor is reset to backend state and revisionId is updated. Dirty-flag optimization: Save button disabled if no edits since last save (nice-to-have, optional). UI states: loading (during save request), error-recoverable (409 conflict, offer user choice), error-unrecoverable (5xx or network error, show error, keep Save enabled for retry), success-transient (200 response, show 'Saved' for 1-2 seconds).

**Backend Impact (Tweedledum):**

Schema: no new columns (revision_id is computed). Endpoints: (1) Compute revision_id = SHA256 hash of [title, body, sorted_tag_ids, updated_at] on every response. (2) Validate If-Match header on PUT; return 409 if mismatch with current revision. (3) Audit trail logs revision_id with each save. Estimate: ~3 hours (hash computation, If-Match validation, audit table schema, test coverage). Complexity: low (standard optimistic locking pattern, no distributed consensus needed).

**Conflict Response Contract (409 Conflict):**

When PUT /api/notes/{id} with If-Match header detects a mismatch, return HTTP 409 Conflict with response body:
```json
{
  "detail": {
    "error": "ConflictError",
    "message": "Note has been updated since you last synced. Please review the server version and retry.",
    "server_revision_id": "<current_revision_id>",
    "server_state": { <full note object with revision_id> }
  }
}
```

**Non-negotiable contract terms:**
- `error` field is always the string `"ConflictError"`
- `message` field is ALWAYS present and ALWAYS a human-readable string (non-empty). It is NOT optional. Examples: "Note has been updated since you last synced...", "Conflict detected". 
- `server_revision_id` is the current revision_id of the note on the server at conflict time
- `server_state` is the full note object including all fields (id, title, body, tag_names, tag_ids, created_at, updated_at, revision_id)
- FastAPI wraps the HTTPException detail in a top-level `detail` field (implicit in FastAPI behavior)

Client contract: Client must unwrap the `detail` field before parsing the ConflictError. Since message is guaranteed to be present, clients should NOT include fallback defaults (`message || 'Conflict detected'`). If message is missing, it indicates a backend bug, not a missing optional field.
