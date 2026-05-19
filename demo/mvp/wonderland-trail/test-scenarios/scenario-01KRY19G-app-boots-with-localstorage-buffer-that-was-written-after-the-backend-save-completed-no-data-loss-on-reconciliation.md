## Scenario 254: App boots with localStorage buffer that was written AFTER the backend save completed — no data loss on reconciliation

**GUID:** 01KRY19G98KE8SJKZ3Z7K85J7W
**Severity:** silent-wrongness

**Setup:**

Kohl writes a note, clicks save (it atomically writes to backend with revision ID 5). The save completes. Kohl types more text (buffer writes locally). She closes the tab before a second save. localStorage now has the extended content. Backend has content from revision 5.

**Trigger:**

App boots. Frontend fetches backend (revision 5) and checks localStorage. localStorage has newer timestamp and more content.

**Expected:**

Frontend displays the localStorage content (the extended text after the save), shows it as unsaved, and gives Kohl a save button. No content is discarded.

**Concern:**

The reconciliation logic might only look at revision IDs and assume 'if backend has revision 5, we're good.' It might discard the localStorage buffer, losing the post-save keystrokes. Or it might trust localStorage mod time but not show the diff, so Kohl saves not knowing what she's saving.

**Property:**

If (backend_timestamp < localstorage_timestamp AND both can be merged without conflict), always show the localStorage content as the working version and require explicit save to persist it.

**Implies:**
- Implies revision ID alone is not enough — timestamps are needed. Flag for Tweedledum (backend contract).
