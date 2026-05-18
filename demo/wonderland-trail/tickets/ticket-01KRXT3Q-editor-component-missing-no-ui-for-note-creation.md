## Ticket 019: Editor component missing — no UI for note creation

**GUID:** 01KRXT3QPEFT5S5QAN229F25QD
**Sources:** kohl-can-create-and-save-experimental-notes-with-title-and-body, frontend-note-editor-component-not-implemented-feature-001-cannot-ship
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** review_synthesis
**Test design:** skip
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``frontend-note-editor-component-not-implemented-feature-001-cannot-ship`` (block):

**Concern:** A feature is not shipped until both backend and frontend are present and wired. The backend is correct. The frontend is absent. Kohl cannot create notes because there is no UI.

**Request:** Tweedledee: implement Editor component with title text input (1-255 chars), body textarea (markdown, max 16384 chars), Save button, localStorage keystroke buffer (write on keystroke, restore on mount, clear after successful save). Wire Save button to POST /api/notes with {title, body, tag_names: []}. On success, display saved note and clear editor. On error (4xx, 5xx), show error and preserve state. On page reload, restore from localStorage if it exists. Replace App.tsx to render the Editor (this is Ticket 007).

**Location:** ``src/frontend/App.tsx (entire file)``

**Acceptance:**
- Tweedledee: implement Editor component with title text input (1-255 chars), body textarea (markdown, max 16384 chars), Save button, localStorage keystroke buffer (write on keystroke, restore on mount, clear after successful save). Wire Save button to POST /api/notes with {title, body, tag_names: []}. On success, display saved note and clear editor. On error (4xx, 5xx), show error and preserve state. On page reload, restore from localStorage if it exists. Replace App.tsx to render the Editor (this is Ticket 007).
