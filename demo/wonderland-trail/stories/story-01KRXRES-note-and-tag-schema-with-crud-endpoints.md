## Story 006: Note and Tag schema with CRUD endpoints

**GUID:** 01KRXRESM8FPT4WS5G1GDZ6QKK

**Persona:** developer (Kohl's local runtime)

**Situation:**

The developer has cloned the repo and run `uvicorn src.backend.main:app --reload`. The frontend skeleton is ready. But the backend still has placeholder HelloMessage models and messages endpoints — they need to be replaced with actual Note and Tag models that will back Kohl's notebook.

**Need:**

As a developer setting up the local notebook runtime, I need the backend to expose Note CRUD endpoints (create, list, update, delete) and tag associations so the frontend can persist Kohl's captured findings to SQLite.

**Acceptance:**
- Note model exists with fields: id, title, body (markdown text), created_at, updated_at
- Tag model exists with fields: id, name
- Note-to-Tag relationship is many-to-many (a note can have zero or more tags)
- POST /api/notes creates a note with title, body, optional tag_ids array; returns id + created_at
- GET /api/notes lists all notes (payload: array of {id, title, body, tags, created_at, updated_at})
- PATCH /api/notes/{id} updates title, body, or tag_ids; returns updated note
- DELETE /api/notes/{id} removes the note
- All endpoints handle SQLite constraints and return meaningful errors (400 for validation, 404 for missing note)

**Tier:** core

**Confusion-flags:**
- Unclear whether tag_ids on POST should be a flat array or a nested structure — I'm assuming flat array [1, 2, 3] for simplicity.
- Unclear whether listing notes should be paginated or all-at-once — I'm assuming all-at-once for v1 single-device.
- Need to decide: when a note is deleted, should its orphaned tags be cleaned up, or should tags persist independently? I'm leaning toward independent (tag is a first-class thing), but that's a schema decision the backend author should confirm.

**Realizes requirements:**
- core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
- single-operator-notebook-with-no-authentication-or-setup
