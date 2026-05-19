## Ticket 007: Frontend: Editor pane with title input, markdown body editor, and keystroke buffer to localStorage

**GUID:** 01KRXRNHX5PSM0YXPN7RV91FHQ
**Sources:** kohl-can-organize-notes-with-tags-and-read-them-in-markdown-preview, editor-pane-with-title-markdown-body-input-and-localstorage-keystroke-buffer
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1.5–2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: backend-note-and-tag-crud-endpoints-with-schema
- Soft: frontend-markdown-preview-pane-with-live-rendering

**Description:**

Build React Editor component with two input fields: title (text input, single-line) and body (textarea or markdown editor library like react-markdown). On every keystroke in either field, buffer the state to localStorage under a stable key (e.g., 'editor_draft'). On component mount, restore from localStorage if present. Include a 'Save' button that posts the current editor state to POST /notes (or PUT /notes/:id if editing an existing note). Clear localStorage after successful save. Do not render markdown preview in this ticket (that is a separate component).

**Acceptance:**
- Title input field accepts text; updates in real-time as user types
- Body textarea accepts markdown text; updates in real-time as user types
- After each keystroke in either field, the combined state {title, body} is written to localStorage
- On page reload, the editor restores title and body from localStorage
- Save button calls POST /notes with {title, body} and displays success or error
- After successful save, localStorage is cleared
- Editor works without the markdown preview pane (preview is not a hard dependency for this ticket to ship)
- vitest tests cover localStorage read/write, component mount/restore, and save button interaction

**Risk:**

If localStorage quota is a concern or if markdown editor library choice is contentious, default to plain textarea and defer library selection to M5 contract negotiation. If Save button flow needs auth or session context, scope to v1 basics (no auth) and fast-follow full auth integration.
