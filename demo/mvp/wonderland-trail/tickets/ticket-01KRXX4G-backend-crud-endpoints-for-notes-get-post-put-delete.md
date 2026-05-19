## Ticket 045: Backend: CRUD endpoints for notes (GET, POST, PUT, DELETE)

**GUID:** 01KRXX4GXRYNYAV6Y2WKPTZG5C
**Sources:** kohl-creates-and-saves-experimental-notes-with-markdown-bodies, kohl-creates-a-new-note-and-begins-typing, kohl-saves-a-markdown-note-with-formatting-preserved, kohl-edits-an-existing-note-and-re-saves-it
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: frontend-editor-component-and-localstorage
- Blocked by: backend-schema-note-with-title-body-created-at-updated-at-tags-list
- Soft: —

**Description:**

Implement FastAPI (or Flask) endpoints: POST /api/notes (create), GET /api/notes (list all), GET /api/notes/:id (retrieve one), PUT /api/notes/:id (update title/body/tags), DELETE /api/notes/:id (soft or hard delete per choice). Return JSON. Include basic validation (title required, body can be empty). No authentication in v1. Endpoints are the contract the frontend calls; they ground the Kohl workflow end-to-end.

**Acceptance:**
- POST /api/notes creates a note and returns 201 + the note with id
- GET /api/notes returns all notes as JSON array
- GET /api/notes/:id returns one note or 404
- PUT /api/notes/:id updates and returns the updated note
- DELETE /api/notes/:id returns 204 (or soft-delete equivalent)
- All endpoints validate input (title required, graceful error on bad JSON)

**Risk:**

Validation coverage: if we're lenient on validation, the frontend may send malformed data. Mitigate by having Tweedledee validate client-side in parallel (soft dependency).
