## Story 003: Tag input and display

**GUID:** 01KRXRDES1D2YNVMG16Y6PFVSC

**Persona:** Dev implementing the tag feature — needs a way to capture and store per-note tags

**Situation:**

Kohl is creating or editing a note. She can optionally add zero or more tags (e.g., '#experiment', '#hypothesis', '#blocking-issue'). Tags are stored with the note and survive reload.

**Need:**

As a developer implementing note CRUD, I want a tag input interface (user types tags, presses Enter or clicks Add, tags appear as removable chips) and persistence mechanism, so that notes can be categorized and retrieved by tag later.

**Acceptance:**
- User can type tag text and press Enter (or click Add) to create a tag
- Tags appear as chips/badges with a remove button
- Removing a tag updates the note state immediately
- Tags are stored in localStorage with the note
- Page reload restores tags with the note
- A single note can have zero, one, or many tags

**Tier:** core

**Confusion-flags:**
- What is the tag format? Should tags have special characters (e.g., '#experiment' with hash, or just 'experiment')? The requirements don't specify; the dev should clarify with Kohl during implementation.
- Should tags be validated for length, uniqueness per note, or character restrictions? No spec yet — assume permissive (any string, duplicates allowed) until told otherwise.
- This story is scoped to *input and display* of tags at the note level. Searching/filtering by tags is a future story, not part of M1.

**Realizes requirements:**
- core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
- single-operator-notebook-with-no-authentication-or-setup
