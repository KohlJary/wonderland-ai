## Scenario 309: Kohl's keystroke buffer in localStorage survives a page reload but not a browser crash + restart

**GUID:** 01KRY1BD9QYCM0QJV0RZ20601H
**Severity:** degradation

**Setup:**

Kohl types for 5 minutes. Every keystroke is saved to localStorage. The page is accidentally reloaded (Ctrl+R). The localStorage buffer survives and is hydrated into the editor on page load.

**Trigger:**

Page reload: EditorLayout mounts, reads localStorage['editor_draft'], restores {title, body, tags, lastSyncedAt}.

**Expected:**

Editor state is restored from localStorage. Kohl sees her unsaved edits. If lastSyncedAt is older than the server's updated_at, a 'Restore Draft' button appears to let Kohl choose. If they match, the buffer is silently discarded (no conflict). On the next Save, the buffer is cleared.

**Concern:**

If localStorage is cleared on reload (browser privacy settings), Kohl loses her keystroke buffer. If the restore logic is buggy, old data is displayed instead of fresh server data. If Kohl accidentally clicks 'Load Latest' and loses the buffer, the work is gone forever.

**Property:**

localStorage keystroke buffer recovery
