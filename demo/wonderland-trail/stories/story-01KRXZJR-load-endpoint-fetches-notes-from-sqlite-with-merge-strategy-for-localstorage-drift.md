## Story 025: Load endpoint fetches notes from SQLite with merge strategy for localStorage drift

**GUID:** 01KRXZJRZ7SWB69XK08PXVYNEY

**Persona:** Developer building the backend load handler — needs an endpoint that returns persisted notes and helps the frontend detect if localStorage diverges

**Situation:**

Kohl reloads the page. The frontend has notes in localStorage (from keystrokes) and needs to fetch the authoritative state from the backend. If localStorage has unsaved edits and the backend has a more recent save from another tab, the frontend needs to merge correctly.

**Need:**

As a developer, I want a GET /notes endpoint (or /notes/{id}) that returns all persisted notes with revision IDs, so that the frontend can fetch the durable state and merge it intelligently with localStorage, favoring the backend as source of truth when conflict arises.

**Acceptance:**
- GET /notes returns all notes for the single operator with their full state (title, body, tags, created_at, updated_at)
- Each note includes a revision ID (hash of the persisted state) for collision detection
- GET /notes includes a 'last_modified_at' timestamp per note so frontend can detect if backend has newer saves than localStorage
- Response is ordered by updated_at descending (newest first) to align with Kohl's search/list expectations
- Endpoint is fast enough for ~500 notes (no N+1 queries, efficient serialization)

**Tier:** core

**Confusion-flags:**
- Unclear whether GET /notes should return paginated results or all notes at once. At ~500 notes, pagination is probably overkill, but we should decide in the contract.
- Not sure if the revision ID from GET should match the revision ID returned by the save endpoint — it should, but the contract needs to make that explicit.
- Unclear whether tags should be nested in the note object or returned separately. The prior ticket called this out as a contract mismatch (tags array vs. tag IDs vs. tag names). This needs resolution in M3 contract negotiation.

**Realizes requirements:**
- keystroke-level-persistence-with-dual-layer-strategy
- core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
- list-notes-in-reverse-chronological-order-most-recently-edited-first
