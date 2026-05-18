## Story 027: Collision detection via revision ID: prevent silent overwrites when multiple tabs save concurrently

**GUID:** 01KRXZJRZ7SWB69XK08PXVYNF0

**Persona:** Developer implementing collision detection — needs to ensure that if two tabs try to save the same note with different content, the system warns Kohl rather than silently overwriting

**Situation:**

Kohl has Tab A and Tab B both editing the same note. She saves in Tab B. If Tab A then tries to save, the backend should detect that Tab B's revision is now newer and return a collision signal. The frontend (per story 019) will then warn Kohl. The backend's job is to detect the collision and provide the data the frontend needs to resolve it.

**Need:**

As a developer, I want the save endpoint to accept the note's revision_id (from the last Load) and compare it to the backend's current revision_id. If they don't match, return a collision response (409 Conflict or 422 Unprocessable Entity) with the newer revision's state, so that the frontend can warn Kohl and let her choose to proceed or load the newer version.

**Acceptance:**
- Save endpoint requires the client to include the note's current revision_id in the request
- Before writing, the endpoint compares the client's revision_id to the backend's current revision_id for that note
- If they match, the save proceeds and a new revision_id is computed and returned
- If they don't match (collision detected), the endpoint returns a 409 Conflict response with the current backend state and revision_id, without modifying the note
- The audit log includes an entry for every save attempt, including those that fail due to collision (with 'conflict_detected' marker)

**Tier:** core

**Confusion-flags:**
- Unclear whether the client should include the revision_id in the request body or as a header/query param. The contract should specify.
- Not sure if collision should block the save entirely, or if the backend should merge the changes (more complex, out of scope for v1). Assume block-and-return-newer for v1.
- Unclear whether the endpoint should auto-retry or force the client to retry. Assume force-client for v1.

**Realizes requirements:**
- multi-tab-write-collision-must-be-detected-and-surfaced-before-silent-overwrite
- audit-trail-revision-identifier-must-use-deterministic-cryptographic-hash-of-saved-state
- client-keystroke-buffer-must-not-be-trusted-for-conflict-resolution
