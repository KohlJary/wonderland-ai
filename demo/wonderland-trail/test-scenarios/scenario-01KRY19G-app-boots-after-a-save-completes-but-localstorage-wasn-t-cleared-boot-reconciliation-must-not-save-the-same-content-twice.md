## Scenario 255: App boots after a save completes, but localStorage wasn't cleared — boot reconciliation must not save the same content twice

**GUID:** 01KRY19G98KE8SJKZ3Z7K85J7X
**Severity:** degradation

**Setup:**

Kohl writes and saves a note. The save endpoint returns success and revision ID 5. The frontend clears localStorage (standard behavior). Kohl writes more text and the browser crashes before that text is saved or buffered. On reboot, localStorage is empty (cleared after the last save), backend has revision 5.

**Trigger:**

This is the happy path. App boots, fetches backend revision 5, localStorage is empty.

**Expected:**

App displays backend content, no prompt, no duplicate save attempts.

**Concern:**

This case is straightforward, but I want to make sure the reconciliation code doesn't have a bug where it unconditionally saves whatever it finds, even if the backend version already has that exact revision.

**Property:**

If localStorage is empty or has same content as backend, the app must not issue a save request.
