## Scenario: If-Match validation catches multi-tab collision — Tab A saves, Tab B's stale If-Match is rejected with 409

**Severity:** breakage

**Setup:**

Two browser tabs, both editing the same note (id=42):
- Tab A and Tab B both issue GET /notes/42 at time T0.
- Server responds with note including revision_id='hash_old'.
- Both tabs cache revision_id='hash_old' in their local state.
- Tab A edits the title to 'New Title' and clicks Save.
- Tab B is still in the middle of editing (has not saved yet).

**Trigger:**

(1) Tab A sends PUT /notes/42 with body={title: 'New Title', body: '...', tag_ids: [...]} and header If-Match: hash_old.
(2) Backend succeeds: computes new revision_id='hash_new', writes the note, returns 200.
(3) Tab B now sends PUT /notes/42 with body={title: 'Different Title', body: '...', tag_ids: [...]} and header If-Match: hash_old (still the stale revision_id it cached).

**Expected:**

At step (3):
- Backend compares: server's current revision_id='hash_new' vs. If-Match header value='hash_old'.
- They do not match.
- Backend rejects the save with **409 Conflict**.
- Response body includes: {error: 'ConflictError', server_revision_id: 'hash_new', server_state: {...full current note...}}.
- **The note is NOT modified.** It still has title='New Title' from Tab A's save.
- No entry is written for Tab B's attempted save (or audit log marks it as collision_detected=true).

**Concern:**

This is the core bug that revision_id prevents. If the backend does **not** validate If-Match, or validates it but **proceeds with the save anyway** (returns 409 but still updates the note), then Tab B silently overwrites Tab A's edits. Kohl loses work without any warning. This is silent-wrongness: the system appears to work (both saves complete), but one user's edits vanish.

**Property:**

For all concurrent save attempts on the same note: if save_A completes with If-Match=R_old producing note_state N' with revision_id=R_new, and then save_B is attempted on the same note with If-Match=R_old, the system MUST reject save_B (return 409 Conflict, do NOT modify the note) when R_old != R_new.

**Implies:**

Implies architecture: PUT /api/notes/{id} endpoint must validate If-Match header before applying any changes. The validation must happen atomically with the write (no TOCTOU race condition between checking the revision_id and writing the note).

Implies API contract: If-Match header must be required on PUT requests. Missing If-Match should be treated as an error (400 Bad Request or auto-fail with 409).

Implies test: write a test that simulates concurrent PUTs from two connections and verifies one succeeds, one fails with 409, and the note reflects only the first save.
