## Ticket 061: localStorage keystroke buffer with debounce

**GUID:** 01KRY06RWJVEFDZG541GV8WNBS
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, 01HNQ8X2PHQBNK3R8GYV7ZQMSE:kohl-drafts-and-saves-experimental-notes-with-persistent-backup, 01KRXRDES1D2YNVMG16Y6PFVSA:localstorage-backed-note-state-layer, 01KRXRESM8FPT4WS5G1GDZ6QKM:editor-pane-with-title-markdown-body-input-and-localstorage-keystroke-buffer, 01KRXRFV251BRQPQMWQTZBXJSX:developer-can-persist-editor-state-to-localstorage-so-keystrokes-survive-page-reload
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1-2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: save-button-integration-with-backend
- Blocked by: —
- Soft: —

**Description:**

Implement a React hook that syncs the editor's title and body state to localStorage on every keystroke (with 300ms debounce to avoid thrashing). On mount, restore from localStorage if present, falling back to empty note. This is the client-side durability layer that survives page reload.

**Acceptance:**
- On every keystroke in title or body, localStorage.setItem('noteBuffer', {title, body, revisionId}) is called within 300ms
- On component mount, the editor populates from localStorage if present; empty localStorage results in empty title/body
- Page reload restores the buffered content without API call
- localStorage read errors don't crash the app (catch and log, proceed with empty state)

**Risk:**

If debounce is too short, localStorage thrashing may cause performance degradation on slower devices. If debounce is too long, risk of data loss on sudden crash. 300ms is a reasonable middle ground but should be tuned after first integration test.
