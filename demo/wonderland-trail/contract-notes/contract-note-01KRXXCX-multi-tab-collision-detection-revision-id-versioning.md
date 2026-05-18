## Contract Note 012: Multi-tab collision detection: revision_id versioning

**GUID:** 01KRXXCXPYSGNTH23Q2E95RYR4
**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

Contract-note-003 references If-Match header but doesn't define what the version value is.

**Proposed Change:**

Every note response (POST, PUT, GET) includes revision_id: string (opaque, computed server-side). Semantics: revision_id is a hash of [title, body, sorted_tag_ids, updated_at]. When any of these properties change on the server, revision_id changes. Client caches revision_id after a successful save. On the next PUT, client sends If-Match: <cached_revision_id> header. If the server's current revision_id matches, update proceeds (200). If not, server returns 409 Conflict with {error: 'ConflictError', server_revision_id: <current>, server_state: full note including new revision_id}. This lets the client detect multi-tab/multi-device edits and warn the user. v1 does not auto-merge; user chooses (overwrite or accept server version).

**Source:** Tweedledee Q3 (multi-tab collision detection).

**Frontend Impact (Tweedledee):**

I cache revision_id after every successful save (POST or PATCH response). On the next PATCH, I include If-Match header with the cached revision_id. If response is 409 Conflict, I parse {error, server_revision_id, server_state} and emit a collision event (to be handled by Story 027 collision-detection flow). For v1, user chooses: Overwrite (re-PATCH with If-Match: <new server_revision_id>) or Accept Server Version (abandon draft, reload editor with server_state). Collision event bubbles to App level for UI modal.

**Backend Impact (Tweedledum):**

Compute revision_id on each note response. Validate If-Match header on PUT, return 409 if mismatch. No schema changes (revision_id is computed, not stored). Estimate: ~2 hours (add hash computation + validation logic).
