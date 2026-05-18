## Ticket 046: Frontend: Editor component (title input, body textarea) + localStorage sync

**GUID:** 01KRXX4GXRYNYAV6Y2WKPTZG5D
**Sources:** kohl-creates-and-saves-experimental-notes-with-markdown-bodies, kohl-creates-a-new-note-and-begins-typing, kohl-saves-a-markdown-note-with-formatting-preserved, kohl-edits-an-existing-note-and-re-saves-it
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1.5–2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: backend-schema-note-with-title-body-created-at-updated-at-tags-list
- Soft: backend-crud-endpoints-notes

**Description:**

Build a React component (or vanilla JS, per project convention) with title input field and body textarea. On keystroke, debounce and serialize to localStorage under a session key (e.g., 'draft:current'). On component mount, restore from localStorage if present. On save button click, POST to /api/notes (or PUT if editing an existing note). Clear localStorage after successful save. Include basic UX: unsaved indicator, save button, "create new" button. No markdown rendering in the editor itself (that's the next ticket).

**Acceptance:**
- Editor component renders with title input and body textarea
- Keystroke to body textarea triggers localStorage write (after 500ms debounce)
- Page reload restores the draft from localStorage
- Save button POSTs to /api/notes (backend must be ready)
- After successful save, localStorage draft is cleared
- Unsaved indicator shows when draft differs from last saved version
- "Create new" button clears the editor and localStorage

**Risk:**

localStorage behavior is browser-specific; we may hit quota limits or private-browsing mode restrictions. Mitigate by graceful fallback (warn user, don't crash). Debounce timing: too fast floods localStorage, too slow loses recent keystrokes—aim for 500ms and adjust based on user feedback during demo.
