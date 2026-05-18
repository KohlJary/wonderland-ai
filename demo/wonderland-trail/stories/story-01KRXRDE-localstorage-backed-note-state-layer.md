## Story 001: localStorage-backed note state layer

**GUID:** 01KRXRDES1D2YNVMG16Y6PFVSA

**Persona:** Dev setting up the notebook — needs durable keystroke buffering

**Situation:**

Developer opens the editor and starts typing. The keystroke stream (title + body + tags) must survive page reload and browser restart without backend persistence.

**Need:**

As a developer maintaining this codebase, I want note state (title, markdown body, tags) to persist to localStorage on every keystroke, so that Kohl's work is resilient to page reload and doesn't require a running backend.

**Acceptance:**
- Note state (title, body, tags) syncs to localStorage on every edit
- Page reload restores the note state from localStorage
- localStorage read/write errors don't crash the app (graceful fallback or user warning)
- Typing performance is not degraded (debounce if needed to avoid thrashing storage)

**Tier:** core

**Confusion-flags:**
- How often should we write to localStorage — every keystroke or debounced? The acceptance criteria say 'every keystroke' but performance might argue for debounce. This tradeoff should be resolved in M2 before implementation.
- Should we persist the full note state as one JSON blob, or split title/body/tags into separate keys? Blob is simpler; split is more granular. The client-side schema should make this obvious.
- Should there be a localStorage quota strategy? No plan yet for 'localStorage is full' — just noting it as a risk for future sprints.

**Realizes requirements:**
- offline-capable-app-with-client-side-markdown-rendering
- core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
- single-operator-notebook-with-no-authentication-or-setup
