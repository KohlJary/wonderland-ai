## Scenario 343: Kohl types, the keystroke buffer is written, then she clicks Save—keystroke buffer is cleared

**GUID:** 01KRY1DM2GCZ9MKM8TTD72W1P8
**Severity:** silent-wrongness

**Setup:**

Kohl types 'Test note' into the body field. The keystroke buffer debounce fires and writes {title: '', body: 'Test note', tags: []} to localStorage. Kohl then clicks the Save button, which triggers a POST /api/notes request.

**Trigger:**

The POST /api/notes request succeeds (201 response with the persisted note). The Editor component receives the response and must decide: should it clear localStorage now, or wait?

**Expected:**

The Editor clears localStorage immediately on receiving the 200 response. The keystroke buffer is removed from localStorage so that on next page load, the editor starts fresh (no restored draft because the draft was saved).

**Concern:**

If the keystroke buffer is not cleared after a successful save, a user who saves, closes the tab, and reopens it will see the old draft still in the editor (not the newly saved version). The server has the correct note; the client's localStorage has stale data. On load, the editor should fetch the note from the server (which it does), but if it also restores from localStorage, there's a merge conflict. The test is: does the keystroke buffer get cleared after save succeeds?

**Property:**

keystroke-buffer-cleared-on-save

**Implies:**
- localstorage-is-removed-after-successful-post
- on-reload-after-save-editor-fetches-server-state-not-stale-localStorage
