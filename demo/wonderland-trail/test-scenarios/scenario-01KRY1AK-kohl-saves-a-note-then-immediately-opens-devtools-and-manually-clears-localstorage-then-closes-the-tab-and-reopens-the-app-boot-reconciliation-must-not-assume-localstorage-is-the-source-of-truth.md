## Scenario 297: Kohl saves a note, then immediately opens DevTools and manually clears localStorage, then closes the tab and reopens the app. Boot reconciliation must not assume localStorage is the source of truth.

**GUID:** 01KRY1AKDJCTY1526GW9Z2EK9M
**Severity:** degradation

**Setup:**

Kohl has created and saved a note: 'Experiment Log' with body 'Day 5 observations'. POST /notes succeeded with 200 response. Frontend cleared localStorage after save. She then manually opens DevTools, goes to Application > Storage > localStorage, and deletes the note entry (simulating a cache corruption or user's manual action). Backend still has the note persisted (it's in SQLite).

**Trigger:**

Kohl closes the browser tab and reopens it. The app mounts. Editor.useEffect checks localStorage for a buffered draft.

**Expected:**

localStorage is empty (user deleted it). Editor detects no buffer and calls GET /notes/{currentNoteId}... but wait, currentNoteId is null (this is a 'new note' or 'pick a note from list' scenario, not an edit scenario). So the editor shows a blank editor ready for a new note. If Kohl later navigates to the NoteList and clicks on the saved note she created, the editor then calls GET /notes/{id} and loads the persisted note correctly from the backend. The persisted note is NOT lost; it's just not loaded until Kohl explicitly selects it.

**Concern:**

The boot reconciliation flow must not assume localStorage is canonical. If the app tries to load a note and localStorage is missing but backend has it, the app should load from backend, not crash or show a stale version. If the app is in 'new note' mode (no noteId), and localStorage is also empty, the app should show a blank editor, not error out.

**Property:**

Boot reconciliation tolerates missing or corrupted localStorage by falling back to backend-canonical state.

**Implies:**
- boot-with-missing-localStorage-does-not-crash
- boot-with-noteId-present-loads-from-backend-even-if-localStorage-is-missing
