## Ticket 010: Backend: Note schema definition with SQLite migrations

**GUID:** 01KRXRQFWE62GX0NN36WZ0Q29M
**Sources:** kohl-can-create-and-save-experimental-notes-with-title-and-body
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.5-1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: backend-note-create-read-endpoints, frontend-note-editor-form-with-title-and-body-input
- Blocked by: —
- Soft: —

**Description:**

Define the Note schema in SQLite with fields: id (primary key), title (text, required), body (text, required), created_at (timestamp), updated_at (timestamp). Ship the migration file and schema definition module. This is the contract that frontend and endpoint implementations will depend on.

**Acceptance:**
- SQLite schema migration file exists and is runnable
- Note model module exports schema definition with all required fields
- Migration can be applied and rolled back cleanly
- Schema is documented in a contract file readable by both backend and frontend

**Risk:**

SQLite schema changes mid-flight require migration rewrites; lock this early before endpoints depend on it.
