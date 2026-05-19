## Story 030: Frontend: Revision ID tracking and collision detection flow integration

**GUID:** 01KRXZM1NPKFYDBZHDA4GRTS50

**Persona:** Developer managing note state and revision metadata — needs to track the current revision_id for every note and use it to detect collisions before Save

**Situation:**

Kohl's note has been loaded from the backend with revision_id = 'hash123'. She edits the body. When she clicks Save, the frontend must send revision_id = 'hash123' in the request. The backend compares it to its current revision (which might now be 'hash456' if another tab saved in the meantime) and returns a 409 if they don't match. The frontend receives the 409 and triggers the collision warning flow.

**Need:**

As a developer, I want every Note object in the app state to track its revision_id (the hash from the last Load or Save), so that I can include it in Save requests and detect collisions by interpreting 409 responses from the backend.

**Acceptance:**
- The Note state schema includes a revision_id field (string, hash from backend)
- When a note is loaded from the backend (via Story 029), the revision_id is extracted from the response and stored in app state
- When a note is created fresh in the editor (no backend entry yet), revision_id is null or undefined
- Before calling Save (Story 028), the frontend includes revision_id in the request payload
- If the backend returns 409 Conflict, the frontend extracts the newer note state and newer revision_id from the response body
- The frontend then triggers the collision warning flow (Story 019 — Kohl gets a warning if editing the same note in multiple tabs) with the newer state as context
- On 200 success, the frontend updates the local revision_id to the new one returned by the endpoint

**Tier:** core

**Confusion-flags:**
- Unclear whether revision_id should be a field in the Note model, or tracked separately in a revision map keyed by note_id. The schema choice affects how the components pass it around. The contract should specify.
- Not sure if the frontend should validate that the revision_id is a valid SHA256 hash, or just pass it through as an opaque string. Probably opaque for now.
- Unclear whether null/undefined revision_id (for newly-created notes) should be handled specially in the Save request, or if the backend should auto-create a record with revision_id = hash of empty state. The contract needs to decide.

**Realizes requirements:**
- multi-tab-write-collision-must-be-detected-and-surfaced-before-silent-overwrite
- audit-trail-revision-identifier-must-use-deterministic-cryptographic-hash-of-saved-state
- client-keystroke-buffer-must-not-be-trusted-for-conflict-resolution
