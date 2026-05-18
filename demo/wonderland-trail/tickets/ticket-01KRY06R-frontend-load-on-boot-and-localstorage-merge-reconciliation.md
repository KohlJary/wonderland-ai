## Ticket 066: frontend load-on-boot and localStorage merge reconciliation

**GUID:** 01KRY06RWJVEFDZG541GV8WNBY
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, 01HNQ8X2PHQBNK3R8GYV7ZQMSE:kohl-drafts-and-saves-experimental-notes-with-persistent-backup, 01KRXZM1NPKFYDBZHDA4GRTS4Z:frontend-load-on-boot-integration-with-backend-notes-endpoint-and-localstorage-merge
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1.5-2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: backend-load-get-notes-endpoint, frontend-revision-id-tracking
- Soft: —

**Description:**

Implement app boot sequence (useEffect on root component) that calls GET /notes, fetches persisted notes, and merges each one with any corresponding localStorage keystroke buffer by comparing revision_id. If backend revision is newer OR localStorage has no entry, load backend version. If localStorage is newer (unlikely, but possible with clock drift), keep localStorage but log a warning. Update app state with merged notes. Ensure Editor component receives the merged note's revision_id for the next Save call. If backend is unreachable, fall back to localStorage gracefully without crashing.

**Acceptance:**
- On app boot (App component useEffect), a loadNotes() call is triggered (async)
- loadNotes() calls GET /notes and waits for response
- For each persisted note, compare its revision_id to the corresponding localStorage entry's revision_id (if any)
- If backend revision is newer (or localStorage has no entry), use backend version; if localStorage is newer, use localStorage and log a warning
- App state (notes list) is updated with the merged result
- Editor component receives the merged note's revision_id (for use in the next Save call)
- If GET /notes fails (network error, 5xx), the app falls back to localStorage gracefully — notes are populated from localStorage and the user can continue editing
- A subtle status indicator shows 'syncing...' during the load, and 'synced' or error status after

**Risk:**

If the merge logic is loose, Kohl could lose recent edits if the backend version is unexpectedly newer. Recommend implementing a conflict warning (similar to save collision) if the backend is significantly newer than localStorage. Also recommend testing with simulated network delays to ensure the UI doesn't freeze.
