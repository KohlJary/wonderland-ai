## Scenario 054: Kohl's browser is in a low-storage state and localStorage quota is hit mid-edit

**GUID:** 01KRXTBSX1SQXPMXS4J54GRZBR
**Severity:** degradation

**Setup:**

Kohl opens the editor and begins typing. Her device has ~100KB free storage. localStorage quota is 5MB. She has already filled ~4.9MB of her quota with other app data (old cached notes, session data, etc.). She's typing into a new note.

**Trigger:**

Kohl types 250 words (body field). The keystroke buffer tries to write to localStorage, but the quota is exceeded. The write fails silently (browsers don't throw loud errors on quota exceeded for localStorage.setItem).

**Expected:**

One of: (a) the editor displays a subtle warning: 'Storage full. Please save or clear old drafts.' And continues to function (text stays in the editor's React state even if not persisted to localStorage). OR (b) the editor silently degrades — text stays in the editor, keystroke buffering is skipped, but the editor remains usable. Kohl can still click Save to persist to the server. OR (c) the Save button works even though localStorage failed, allowing Kohl to recover her work by persisting to the backend.

**Concern:**

If the editor crashes or throws an exception when localStorage quota is exceeded, Kohl loses access to the editor entirely (screen goes blank or shows error). Or if the editor silently fails to save without warning, Kohl types for 10 minutes, clicks Save, and realizes the save succeeded but her keystroke buffer was never captured — she lost any offline recovery option (though the server save succeeded, so she doesn't lose the work, but the feature feels broken).

**Property:**

editor degrades gracefully when localStorage quota is exceeded

**Implies:**
- localstorage-quota-is-exceeded-device-is-low-on-storage-save-fails-silently-or-degrades-gracefully
