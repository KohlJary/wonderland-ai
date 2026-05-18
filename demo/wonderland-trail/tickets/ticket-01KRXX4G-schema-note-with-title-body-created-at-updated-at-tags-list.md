## Ticket 044: Schema: Note with title, body, created_at, updated_at, tags list

**GUID:** 01KRXX4GXRYNYAV6Y2WKPTZG5B
**Sources:** kohl-creates-and-saves-experimental-notes-with-markdown-bodies, kohl-creates-a-new-note-and-begins-typing, kohl-saves-a-markdown-note-with-formatting-preserved, kohl-edits-an-existing-note-and-re-saves-it
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.5 days, 85% confident
**Status:** open

**Dependencies:**
- Blocks: backend-crud-endpoints-notes, frontend-editor-component-and-localstorage
- Blocked by: —
- Soft: —

**Description:**

Define SQLite schema for notes table. Fields: id (primary key), title (text, required), body (text, nullable, markdown), created_at (timestamp), updated_at (timestamp), tags (JSON array stored as text, serialized/deserialized in ORM). Alembic migration. Schema is the contract both Tweedles depend on; ship this first so the frontend can assume the shape early.

**Acceptance:**
- Alembic migration runs without error
- SQLite schema includes all five fields with correct types
- ORM model (SQLAlchemy or equivalent) reflects the schema
- Migration is reversible

**Risk:**

None anticipated; this is straightforward schema work.
