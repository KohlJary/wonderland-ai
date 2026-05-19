## Story 009: Tag input and association in the editor

**GUID:** 01KRXRESM8FPT4WS5G1GDZ6QKP

**Persona:** developer (Kohl's UI runtime)

**Situation:**

Kohl is writing a note, but she has no way to add tags. The editor form needs to accept tags as comma-separated strings or as a tag picker, and associate them with the note when it's saved.

**Need:**

As a developer building Kohl's UI, I need a tag input component that lets Kohl type or select tags, so she can organize her findings by topic (e.g., 'experiment-A', 'hypothesis-rejected', 'follow-up').

**Acceptance:**
- Editor form includes a tag input field (either comma-separated text or a tag picker UI — author's choice)
- Tags can be entered before the note is saved, and are stored as an array in localStorage alongside title and body
- When the note is saved to the backend, the tag array is sent to the POST /api/notes endpoint
- If a tag doesn't exist in the database, it is created (or rejected with a clear error) — the author should decide the UX
- Tag display shows the tags associated with a note in a readable format (e.g., pill badges, comma-separated list)

**Tier:** core

**Confusion-flags:**
- Should tags be free-form (Kohl types anything) or curated (predefined tag list)? I'm assuming free-form for v1.
- Should the tag input allow multi-select from a dropdown, or just comma-separated text? I'm assuming comma-separated for simplicity.
- Should tags be created on-the-fly (Kohl types a new tag, it's stored) or should the frontend fetch a tag list first? The requirement doesn't specify, so I'm assuming on-the-fly.

**Realizes requirements:**
- core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
