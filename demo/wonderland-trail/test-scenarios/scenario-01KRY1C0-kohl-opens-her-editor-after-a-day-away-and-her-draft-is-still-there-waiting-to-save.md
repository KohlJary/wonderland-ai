## Scenario 310: Kohl opens her editor after a day away and her draft is still there waiting to save

**GUID:** 01KRY1C0REHH0KMQPVA6ED258E
**Severity:** silent-wrongness

**Setup:**

Kohl wrote a 500-word draft on Tuesday evening, hit the browser back button before saving (keystroke buffer is in localStorage). Wednesday morning she opens the app. The backend has no saved note yet (she never clicked Save). localStorage has the unsaved draft with lastSyncedAt = null (never successfully saved).

**Trigger:**

App mounts. useEffect on App component calls loadNotes(). GET /notes returns empty array (no saved notes yet).

**Expected:**

Editor initializes with the Tuesday draft restored from localStorage. The Save button is visible and clickable. Kohl can immediately see her work and save it without re-typing. The UI briefly shows 'Loading notes...' during the fetch, then clears.

**Concern:**

If localStorage is cleared on mount (per naive implementation), Kohl loses the Tuesday draft. The keystroke buffer's whole point is recovery from accidental page closes without save. Silent loss of draft is the worst failure mode.

**Property:**

localStorage keystroke buffer is the source of truth when no backend note exists yet (new draft, never saved).

**Implies:**
- localStorage is only cleared after successful 200 response from POST /notes
- Editor component restores from localStorage if present, regardless of backend state
