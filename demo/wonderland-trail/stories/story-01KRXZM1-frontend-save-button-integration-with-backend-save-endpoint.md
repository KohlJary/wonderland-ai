## Story 028: Frontend: Save button integration with backend /save endpoint

**GUID:** 01KRXZM1NPKFYDBZHDA4GRTS4Y

**Persona:** Developer building the Save button handler — needs to orchestrate the button click, backend call, response handling, and UI feedback

**Situation:**

Kohl clicks the Save button in the editor. The frontend needs to send the current localStorage note state to the backend, handle success (with feedback UI), handle failure (network error, validation error, collision), and update local state accordingly.

**Need:**

As a developer, I want the Save button click to trigger an async POST to /notes/{id} (or /notes) with the current note state and revision_id, so that Kohl's work is persisted to SQLite and she receives clear feedback on success or failure.

**Acceptance:**
- Clicking Save button triggers a saveNote() call with the current note state (title, body, tags) and the note's revision_id from the last Load
- The frontend sends POST /notes (for create) or PUT /notes/{id} (for update) with the payload
- On 200/201 success response, the UI shows a brief success message and updates the note's local revision_id to the new one from the response
- On 409 Conflict response, the frontend emits a 'collision' event (picked up by Story 027 — collision detection flow)
- On network error or 5xx, the UI shows an error message and keeps the save button enabled for retry
- Save button is disabled while a save is in flight (prevent double-submit)
- The editor's localStorage buffer is NOT cleared on save — keystroke edits continue to buffer, allowing save + continue editing flow

**Tier:** core

**Confusion-flags:**
- Unclear whether the endpoint should auto-increment note.id if the note doesn't yet exist on the backend, or if the frontend must generate a stable note ID upfront. The contract (Story 024) needs to specify.
- Not sure if the success response should return the full saved note (for updating Kohl's local copy) or just the new revision_id (lighter payload). The contract should decide.
- Unclear whether Save should be disabled if there are no unsaved changes (dirty flag optimization) — probably yes, but the Editor component needs to track this state.

**Realizes requirements:**
- keystroke-level-persistence-with-dual-layer-strategy
- core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
- saved-state-audit-trail-required-for-each-note-write-to-backend
