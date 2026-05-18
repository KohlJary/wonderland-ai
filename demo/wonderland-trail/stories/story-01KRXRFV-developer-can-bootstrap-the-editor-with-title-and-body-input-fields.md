## Story 010: Developer can bootstrap the editor with title and body input fields

**GUID:** 01KRXRFV251BRQPQMWQTZBXJSV

**Persona:** Dev Maya: frontend engineer setting up the notebook editor component. She clones the repo, runs `npm run dev`, and sees a working editor that accepts a note title and markdown body as text input. She's establishing the baseline UI for Kohl's typing.

**Situation:**

Maya is wiring up the first React component that will hold Kohl's note-taking experience. The App.tsx placeholder exists; it's now her job to replace it with a real editor that captures input.

**Need:**

As Maya, I want the editor component to accept a title field and a markdown body field, so that Kohl can start typing notes into a structured form.

**Acceptance:**
- A React component <Editor /> renders with two input regions: title (single-line) and body (multi-line textarea)
- Both fields accept typed text without backend calls — the keystroke happens client-side
- The form does not submit anywhere yet (no persistence logic); it's just accepting input
- Developer can see the editor in the browser after `npm run dev` with no console errors

**Tier:** core

**Confusion-flags:**
- Not yet clear whether the editor is one note at a time or a note list + detail view. Assuming single-note-focused for now (Kohl edits one note; switching notes is a follow-on story).
- Title field width/height not specified — using sensible defaults (single-line input for title, reasonable textarea for body).

**Realizes requirements:**
- core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
