## Story 004: Replace HelloMessage scaffolding with Note model

**GUID:** 01KRXRDES1D2YNVMG16Y6PFVSD

**Persona:** Dev migrating the ORM layer — needs to remove template code and introduce real models

**Situation:**

The codebase has a placeholder HelloMessage model + API + tests. This scaffolding served the seed; now it needs to be replaced with the actual Note model (title, body, tags, created_at, updated_at).

**Need:**

As a developer maintaining the backend, I want to replace the placeholder HelloMessage with a Note model representing the notebook's core entity, so that the ORM, API, and test layer are all aligned with the actual feature scope.

**Acceptance:**
- HelloMessage class is deleted from src/backend/models.py
- Note model is defined with columns: id (PK), title, body (markdown), tags (JSON or string list), created_at, updated_at
- src/backend/api/messages.py is replaced with a notes_router
- tests/test_messages.py is replaced with tests/test_notes.py
- The backend still exposes a working /health endpoint (no regression)
- All imports and references are cleaned up — no dangling HelloMessage references

**Tier:** core

**Confusion-flags:**
- Should tags be stored as a JSON array in a single column, or as a separate `NoteTag` join table? For a single-device, single-user app with no tag-search in M1, a JSON field is simpler. But if search is coming soon, a proper table is better. This is an architectural call for the Cat.
- created_at and updated_at should be timestamptz for correctness, but SQLite doesn't have true timezone support. The model should document this limitation or use a workaround (e.g., store ISO strings, or convert to UTC).
- The API endpoints for notes will be specified in M2 (tickets); this story just owns the model migration. Don't implement the full CRUD API yet.

**Realizes requirements:**
- core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
- single-operator-notebook-with-no-authentication-or-setup
