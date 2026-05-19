## Scenario 313: Kohl saves a note, closes the editor, reopens it, and the save is remembered without re-fetching unnecessarily

**GUID:** 01KRY1C0REHH0KMQPVA6ED258H
**Severity:** degradation

**Setup:**

Kohl has a saved note id=42. She loads it in the editor, makes a small edit to the title, clicks Save. POST /notes/42 returns 200 with updated_at=2026-05-18T14:30:00Z, version='hash-v2'. Editor clears localStorage after successful save. Kohl closes the editor tab (or navigates away). She then reopens the editor and navigates back to note 42.

**Trigger:**

Editor component mounts with noteId=42. useEffect checks: is there localStorage? No (cleared after save). Is there a noteId? Yes. Calls GET /notes/42.

**Expected:**

GET /notes/42 returns the saved note with title='Final Title', version='hash-v2'. Editor hydrates. Kohl can immediately see her saved work without any 'unsaved' indicators. The version='hash-v2' is cached for the next potential collision detection.

**Concern:**

If Editor always shows an 'unsaved changes' warning after loading from backend (because it compares against an empty initial state), Kohl would see a false positive and think her save didn't work. Or if the UI re-fetches unnecessarily on every editor open, it wastes bandwidth and introduces delay.

**Property:**

After a successful save, localStorage is cleared, and the next load fetches fresh state from backend without false 'unsaved changes' warnings.

**Implies:**
- localStorage is cleared exactly once after 200 response from POST or PUT
- Editor's initial state after GET /notes/{id} is marked as 'saved' (not 'dirty')
- Dirty flag only activates if user makes subsequent edits after load
