## Ticket 063: audit trail logging on every save with immutable records

**GUID:** 01KRY06RWJVEFDZG541GV8WNBV
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, 01HNQ8X2PHQBNK3R8GYV7ZQMSE:kohl-drafts-and-saves-experimental-notes-with-persistent-backup, 01KRXZJRZ7SWB69XK08PXVYNEZ:audit-trail-logs-every-save-with-full-note-state-and-revision-id
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1-1.5 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: backend-note-model-and-atomic-save-endpoint
- Soft: —

**Description:**

Implement audit_log table and logging hook so that every save endpoint call (success or collision) logs an immutable record: note_id, operator_id, saved_state (full JSON), revision_id, timestamp, collision_detected (bool), conflicting_revision_id (if applicable). Logging happens after the note write succeeds (or fails with collision). Audit log entries are append-only (no update/delete).

**Acceptance:**
- audit_log table exists with columns: id (PK), note_id (FK), operator_id, saved_state (JSON), revision_id, timestamp, collision_detected (bool), conflicting_revision_id (nullable string)
- Every save endpoint call (POST or PUT) logs an audit_log entry after the write (success) or after returning 409 (collision)
- saved_state is the full serialized note object (title, body, tags) — no delta-only encoding
- revision_id matches the revision_id computed for that save
- collision_detected is true only when the endpoint returns 409; conflicting_revision_id is set to the backend's current revision_id in that case
- Audit log entries are immutable (no update/delete endpoints for this table)
- Querying audit_log by note_id returns entries in chronological order (oldest first)

**Risk:**

If saved_state is truncated or partially serialized, forensic reconstruction becomes unreliable. Recommend testing with large notes (10KB+ body) to ensure serialization doesn't fail silently.
