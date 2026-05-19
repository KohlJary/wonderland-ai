## Scenario 317: Kohl types, saves the note to the backend, then reloads the page—localStorage should be cleared so she sees the server version, not the old buffer

**GUID:** 01KRY1CT0KYYZH13BXHBA5K1JJ
**Severity:** silent-wrongness

**Setup:**

Kohl types a note, clicks Save, and the backend returns 200 with the persisted note {id: 1, title: '...', body: '...', createdAt, updatedAt}. The editor clears localStorage as part of the successful save flow.

**Trigger:**

Kohl accidentally closes the editor tab and reopens the project app.

**Expected:**

On page load, localStorage['noteBuffer'] is empty (cleared after save). The editor initializes in create mode (or, if navigated to /notes/1, loads the note from the backend via GET /notes/1). Kohl sees the server version of her note, not a stale buffer.

**Concern:**

If localStorage is not cleared after save, Kohl may reload and see the old buffered content instead of the server version. If the server version was edited by another device (future multi-device feature), the buffer would shadow the authoritative version.

**Property:**

localStorage buffer is cleared after successful save to prevent stale restoration.
