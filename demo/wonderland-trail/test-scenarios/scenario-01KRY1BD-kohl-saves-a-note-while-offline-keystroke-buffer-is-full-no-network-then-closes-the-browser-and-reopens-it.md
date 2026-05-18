## Scenario 305: Kohl saves a note while offline (keystroke buffer is full, no network), then closes the browser and reopens it

**GUID:** 01KRY1BD9QYCM0QJV0RZ20601D
**Severity:** silent-wrongness

**Setup:**

Kohl has typed title='Offline notes' and body='Working without internet' (100 chars) into the editor. The keystroke buffer in localStorage has captured both. Network is down; Save button is tapped but fails with no response (timeout). Kohl closes the tab.

**Trigger:**

Page reload: EditorLayout mounts, reads localStorage buffer, detects the unsaved draft. Then tries GET /api/notes/{id} to compare versions.

**Expected:**

localStorage buffer is preserved across reload (Kohl sees 'Restore Draft' button). Once network returns, Kohl can click Save and the keystroke buffer is flushed to the server. If network is still down, the error is clear: 'Save failed, check your connection' or similar. Kohl's work is not lost.

**Concern:**

If localStorage is cleared on reload, Kohl loses her unsaved work. If the restore logic fails, the old saved version is loaded and the buffer is overwritten. If the offline error message is cryptic, Kohl doesn't know why Save failed.

**Property:**

Offline resilience + keystroke buffer recovery
