## Ticket 062: backend Note model and atomic save endpoint with revision ID

**GUID:** 01KRY06RWJVEFDZG541GV8WNBT
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, 01HNQ8X2PHQBNK3R8GYV7ZQMSE:kohl-drafts-and-saves-experimental-notes-with-persistent-backup, 01KRXRDES1D2YNVMG16Y6PFVSD:replace-hellomessage-scaffolding-with-note-model, 01KRXZJRZ7SWB69XK08PXVYNEX:save-endpoint-persists-note-state-to-sqlite-atomically, 01KRXZJRZ7SWB69XK08PXVYNF0:collision-detection-via-revision-id-prevent-silent-overwrites-when-multiple-tabs-save-concurrently
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 2-3 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: load-endpoint-and-boot-merge, audit-trail-logging
- Blocked by: —
- Soft: —

**Description:**

Implement the Note model (id, title, body, tags, created_at, updated_at) replacing the placeholder HelloMessage. Implement POST /notes (create) and PUT /notes/{id} (update) endpoints that accept title, body, tags array, and revision_id. The endpoint writes the note atomically to SQLite and computes a new revision_id (SHA256 hash of the saved state). If revision_id in the request doesn't match the backend's current revision, return 409 Conflict with the newer state.

**Acceptance:**
- Note model with id (PK), title, body, tags (JSON or array), created_at, updated_at, revision_id (string) exists in src/backend/models.py
- POST /notes accepts {title, body, tags} and returns {id, title, body, tags, created_at, updated_at, revision_id}
- PUT /notes/{id} accepts {title, body, tags, revision_id} and returns the same on 200 success
- If revision_id in request doesn't match backend's current revision_id for that note, return 409 Conflict with current backend state and current revision_id
- Atomic write: note and all tags are persisted in a single transaction or rolled back together on error
- revision_id is computed as SHA256(json.dumps(sorted_note_state)) — deterministic, same state always produces same hash
- HelloMessage model and related API/tests are removed; no dangling references remain
- /health endpoint still works (sanity check)

**Risk:**

Collision detection via revision_id requires careful implementation of the comparison logic. If the hash is non-deterministic, collisions will be detected spuriously. If the transaction logic is loose, partial saves could corrupt the database. Recommend pair review with the Caterpillar.
