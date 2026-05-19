## Ticket 011: Backend: Note create and read endpoints

**GUID:** 01KRXRQFWE62GX0NN36WZ0Q29N
**Sources:** kohl-can-create-and-save-experimental-notes-with-title-and-body
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1-1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: frontend-note-editor-form-with-title-and-body-input
- Blocked by: backend-note-schema-with-sqlite-migrations
- Soft: —

**Description:**

Implement POST /notes (create with title and body) and GET /notes/:id (retrieve by id) endpoints. Both endpoints validate input, interact with the Note schema, and return JSON. Endpoints follow the schema contract from the schema ticket.

**Acceptance:**
- POST /notes accepts title and body, stores in database, returns created note with id and timestamps
- GET /notes/:id retrieves note by id and returns it as JSON
- Both endpoints validate required fields (title and body present and non-empty)
- Endpoints return appropriate HTTP status codes (200, 201, 400, 404)

**Risk:**

Frontend may need error response shape before this ships; consider shipping a contract note early if the shape is unclear.
