## Story 029: Frontend: Load-on-boot integration with backend /notes endpoint and localStorage merge

**GUID:** 01KRXZM1NPKFYDBZHDA4GRTS4Z

**Persona:** Developer building the app's initialization flow — needs to fetch persisted notes from SQLite and merge with any keystroke-buffered edits in localStorage

**Situation:**

Kohl reloads the page (or the app initializes). The frontend needs to fetch the durable note state from the backend, compare it with the localStorage keystroke buffer, and resolve any divergence by favoring the backend as source of truth (but preserving local unsaved edits if they're newer).

**Need:**

As a developer, I want the app's boot sequence to call GET /notes, fetch the persisted notes with their revision IDs, and merge each persisted note's revision_id with the corresponding localStorage entry, so that the app opens with the correct state and Kohl's unsaved buffer isn't wiped out.

**Acceptance:**
- On app boot (App component mounted or useEffect on root), trigger a loadNotes() call that fetches GET /notes
- Parse the response and for each note, compare its revision_id to the localStorage entry's revision_id (if any)
- If backend revision is newer OR localStorage has no entry, load the backend version into the UI
- If localStorage has a newer timestamp (unlikely, but handles clock drift), keep localStorage but warn the developer (log it, don't break)
- Update the app's note list state with the merged result
- Ensure the Editor component has the merged note's revision_id available for the next Save call (Story 028)
- If the backend is unreachable (network error, 500), fall back to localStorage gracefully without crashing the UI

**Tier:** core

**Confusion-flags:**
- Unclear how to compare 'newer' — the backend returns updated_at timestamp and revision_id. Should the frontend use updated_at for the merge decision, or the revision_id hash? The contract should specify the precedence.
- Not sure if 'localStorage has no entry' means the note is brand new in the backend (Kohl created it in another tab), or if it means she never typed it locally. Both cases should load the backend version, but the reasoning is different.
- Unclear whether the frontend should poll for new notes or just load once on boot. Assume load-once for v1; future milestone can add polling or WebSocket push if needed.

**Realizes requirements:**
- keystroke-level-persistence-with-dual-layer-strategy
- list-notes-in-reverse-chronological-order-most-recently-edited-first
- core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
