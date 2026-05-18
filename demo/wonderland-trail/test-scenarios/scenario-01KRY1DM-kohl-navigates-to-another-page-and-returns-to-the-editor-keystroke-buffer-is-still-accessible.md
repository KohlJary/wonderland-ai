## Scenario 345: Kohl navigates to another page and returns to the editor—keystroke buffer is still accessible

**GUID:** 01KRY1DM2GCZ9MKM8TTD72W1PA
**Severity:** degradation

**Setup:**

Kohl opens the editor and types 'Research findings' (50 chars) into the body field. The keystroke buffer writes to localStorage. Kohl then clicks a link in the app to navigate to the notes list page (view changes from 'editor' to 'list').

**Trigger:**

After 30 seconds, Kohl clicks on a note in the list to open it in the editor (navigation back to editor view). The Editor component mounts and useEffect checks for a saved buffer in localStorage.

**Expected:**

The keystroke buffer (from the first editor session) is still in localStorage, but it's from a *different* note context. Kohl had typed into a *new note* (noteId was null), but now she's opening note #42 (noteId=42). The buffer she typed was for a new note, not for note #42. The editor should show note #42's content from the server (via GET /api/notes/42), not the old buffer.

**Concern:**

If the keystroke buffer is not scoped to the noteId, a stale buffer from editing one note may be restored when editing a different note. Degradation: Kohl sees the wrong content (old buffer) instead of the note she clicked. This is not silent (she'll notice the mismatch), but it's a usability problem.

**Property:**

keystroke-buffer-scope-per-note

**Implies:**
- keystroke-buffer-key-includes-noteid
- editor-does-not-restore-buffer-for-wrong-note
