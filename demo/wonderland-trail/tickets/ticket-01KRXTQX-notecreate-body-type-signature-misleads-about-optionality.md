## Ticket 021: NoteCreate.body type signature misleads about optionality

**GUID:** 01KRXTQXFPAKBVMQRQXZ8WWM20
**Sources:** kohl-can-organize-notes-with-tags-and-read-them-in-markdown-preview, backend-note-crud-endpoints-models-and-database
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** review_synthesis
**Test design:** skip
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``backend-note-crud-endpoints-models-and-database`` (change-required):

**Concern:** Future developers reading this schema will think body must be present in the request. When they try to call createNote without a body field, they'll be surprised it works. This is a clarity issue: the type doesn't match the behavior.

**Request:** Change to `body: str | None = Field(default=None, max_length=16384)`. This makes it explicit: body is optional in the request. Then in create_note, do `note.body = payload.body or ""` to ensure the database always gets a string. This separates concerns: the request contract (body optional) from the storage contract (body is always a string).

**Location:** ``src/backend/api/notes.py:50-51``

**Acceptance:**
- Change to `body: str | None = Field(default=None, max_length=16384)`. This makes it explicit: body is optional in the request. Then in create_note, do `note.body = payload.body or ""` to ensure the database always gets a string. This separates concerns: the request contract (body optional) from the storage contract (body is always a string).
