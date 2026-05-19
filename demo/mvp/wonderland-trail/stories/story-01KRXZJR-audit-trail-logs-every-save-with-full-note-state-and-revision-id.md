## Story 026: Audit trail logs every save with full note state and revision ID

**GUID:** 01KRXZJRZ7SWB69XK08PXVYNEZ

**Persona:** Developer building the audit logging layer — needs a durable record of all note saves for forensic reconstruction and collision detection

**Situation:**

Kohl has saved a note. The backend has written it to SQLite, but we also need an audit trail so that if Kohl later claims 'I had content X in my note' or 'why did my edits disappear?', we can reconstruct what happened. Additionally, the revision ID in the audit trail helps the frontend detect conflicts across saves.

**Need:**

As a developer, I want every note save to be logged to an audit_log table with full note state (title, body, tags), timestamp, operator ID, revision ID (cryptographic hash), and any collision detection data, so that we have a complete forensic trail and can implement reliable collision detection.

**Acceptance:**
- Every save endpoint call logs an entry to audit_log with: note_id, operator_id (hardcoded to 'kohl' for v1), saved_state (full JSON), revision_id (SHA256 hash of saved state), timestamp, and any collision detection fields
- Audit log entries are immutable — no update or delete, only insert
- The revision_id is deterministic (same note state always produces the same hash, regardless of save order)
- If a collision is detected (e.g., attempting to save over a note that was already saved by another tab), the audit log includes a 'conflict_detected' marker with the conflicting revision ID
- Audit log can be queried by note_id to reconstruct the full history of saves for that note

**Tier:** core

**Confusion-flags:**
- Unclear whether 'full note state' means the entire serialized note object, or a summary. The ruling says 'full note state' and 'no delta-only encoding' — need to enforce that in the implementation.
- Not sure if we should log the operator_id or just the timestamp. The ruling implies per-operator, but v1 is single-operator. Still, the schema should accommodate multi-operator in the future.
- Unclear whether the audit log should be exposed via an API endpoint (for Kohl to inspect) or kept internal. Probably internal for v1, but the contract should make that clear.

**Realizes requirements:**
- saved-state-audit-trail-required-for-each-note-write-to-backend
- audit-trail-must-be-immutable-and-complete-enough-for-forensic-reconstruction
- audit-trail-revision-identifier-must-use-deterministic-cryptographic-hash-of-saved-state
