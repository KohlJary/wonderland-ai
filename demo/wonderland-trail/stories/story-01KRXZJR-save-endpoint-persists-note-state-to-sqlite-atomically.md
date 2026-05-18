## Story 024: Save endpoint persists note state to SQLite atomically

**GUID:** 01KRXZJRZ7SWB69XK08PXVYNEX

**Persona:** Developer building the backend save handler — needs an endpoint that writes notes and tags to SQLite in a single transaction

**Situation:**

Kohl clicks the Save button in the editor. The frontend sends a POST request with the current note state (title, body, tags). The backend must write this atomically to SQLite so that either the whole note+tags persist together or nothing persists — no partial saves.

**Need:**

As a developer, I want a /notes/{id}/save endpoint (or similar) that accepts a note payload and writes it to SQLite atomically with all associated tags, so that Kohl's saves are durable and never corrupt the database with partial writes.

**Acceptance:**
- POST /notes (or PUT /notes/{id}) accepts title, body, tags in the request body
- Endpoint writes note and all tags to SQLite in a single transaction
- If the transaction fails, the entire write is rolled back — no partial state persists
- Endpoint returns the saved note with a revision ID (hash of the saved state) for collision detection
- The save is logged to the audit trail with full note state, timestamp, and revision ID
- Concurrent saves to the same note are serialized (no race conditions)

**Tier:** core

**Confusion-flags:**
- Unclear whether PUT /notes/{id} (update existing) and POST /notes (create new) are the same endpoint with different payloads, or separate. The contract needs to specify.
- Not sure if the revision ID should be SHA256 of the serialized note state (deterministic) or an incrementing version counter. The audit trail ruling says 'cryptographic hash' — need to enforce that in the contract.
- Unclear whether the endpoint should validate tag IDs or accept tag names and auto-create tags. This affects the request schema.

**Realizes requirements:**
- keystroke-level-persistence-with-dual-layer-strategy
- core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
- saved-state-audit-trail-required-for-each-note-write-to-backend
