## Ticket 006: Backend: Note and Tag CRUD endpoints with schema

**GUID:** 01KRXRNHX4M490DV6X78TYQ1Q5
**Sources:** kohl-can-organize-notes-with-tags-and-read-them-in-markdown-preview, note-and-tag-schema-with-crud-endpoints
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1.5–2.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: frontend-editor-pane-with-title-markdown-body-input-and-localstorage-keystroke-buffer, frontend-tag-input-and-association-in-the-editor, frontend-markdown-preview-pane-with-live-rendering
- Blocked by: —
- Soft: —

**Description:**

Implement SQLite schema for Note (id, title, body, created_at, updated_at) and Tag (id, name). Implement REST endpoints: POST /notes, GET /notes, GET /notes/:id, PUT /notes/:id, DELETE /notes/:id. Implement tag association: POST /notes/:id/tags, DELETE /notes/:id/tags/:tag_id. Endpoints return JSON; POST/PUT accept JSON. Include server-side validation (title required, body optional, tag names unique per note).

**Acceptance:**
- POST /notes creates a note with title and optional body; returns note object with id
- GET /notes returns list of all notes
- GET /notes/:id returns single note
- PUT /notes/:id updates title and/or body
- DELETE /notes/:id removes note
- POST /notes/:id/tags associates an existing or new tag with the note
- DELETE /notes/:id/tags/:tag_id removes tag from note
- Server validates title is non-empty; tag names are non-empty; returns 400 on invalid input
- All endpoints are tested via pytest with at least happy-path + one error case per endpoint

**Risk:**

If tag association table design requires migration or schema refactor mid-ticket, expand to 3 days. If server-side validation logic grows beyond basic presence/type checks, scope it to v1 basics only and fast-follow rich validation.
