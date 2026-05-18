## Implementation 012: NoteCreate.body type signature fix

**GUID:** 01KRXTT84MABHE0TNK2GCGA548
**Side:** backend
**Ticket:** 01KRXTQX
**Contract:** POST /api/notes request envelope v1.1: {title: str, body: str | None = None, tag_names: list[str] = []}. Response unchanged: 201 {id, title, body, tag_names, tag_ids, created_at, updated_at}
**Ready for review:** yes

**Approach:**

Changed NoteCreate model to make body field properly optional (str | None with default=None) instead of misleadingly required (str with default=""). Updated create_note endpoint to convert None to empty string before persisting. This makes the request-side contract explicit and matches database schema (body is NOT NULL, always a string).

**Invariants Enforced:**
- Note.body is always a string (never NULL) in the database — None in request becomes empty string

**Schema Changes:**

No database migration needed — existing body column was already NOT NULL with default='' after prior schema work. Models.py was already updated to reflect this.

**Failure Modes Handled:**
- Client sends body: null — converted to empty string, stored as empty string in database

**Files:**
- src/backend/api/notes.py: NoteCreate model body field type + create_note implementation
