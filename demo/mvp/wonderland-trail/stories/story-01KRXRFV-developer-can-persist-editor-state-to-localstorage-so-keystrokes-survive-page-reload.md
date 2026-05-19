## Story 012: Developer can persist editor state to localStorage so keystrokes survive page reload

**GUID:** 01KRXRFV251BRQPQMWQTZBXJSX

**Persona:** Dev Maya: testing offline resilience. She types a note in the editor, closes the tab or refreshes the page, and sees her content restored. She's verifying that localStorage is the persistence layer for this milestone, and that Kohl's keystrokes are not lost to a page reload.

**Situation:**

The editor + preview are working; now Maya needs to ensure that the data Kohl types is safe across browser sessions. There's no backend persistence yet (that's a later milestone), so localStorage is the only durability guarantee.

**Need:**

As Maya, I want editor state (title and body) to be automatically saved to localStorage on every keystroke, and restored on page load, so that Kohl's work is resilient to page reloads and browser restarts.

**Acceptance:**
- On every keystroke in the title or body field, the editor state is written to localStorage
- On page load, the editor populates with content from localStorage if it exists
- If localStorage is empty (first visit), the editor starts with empty title and body
- Page reload or tab close/reopen does not lose the note content
- The localStorage key is stable and documented (e.g., 'notebook_current_note' or similar)

**Tier:** core

**Confusion-flags:**
- localStorage size limit (~5-10MB per domain) is not a constraint at v1 scale, but should be noted if Kohl's notes grow very large.
- No conflict-resolution logic: this milestone assumes a single editor session (one tab, one user). If Kohl opens multiple tabs, they will clobber each other in localStorage — that's acceptable for single-device-single-user scope, but worth flagging.

**Realizes requirements:**
- single-device-single-user-single-sqlite-file
- offline-capable-app-with-client-side-markdown-rendering
