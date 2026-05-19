## Scenario 369: Kohl's browser tab crashes and restarts. localStorage still has her unsaved keystroke buffer. On reload, she clicks 'Restore Draft' to keep her local changes instead of loading the server version. The draft remains editable and can be saved.

**GUID:** 01KRY1G5562S7JSHVEXACBHXDZ
**Severity:** silent-wrongness

**Setup:**

Kohl had note #42 open, made edits (title: 'Research Log', body: '# Day 1

Started. Baseline observed. Ready for Day 2.'), but did not click Save. The browser tab crashed. localStorage contains {id: 42, title: 'Research Log', body: '# Day 1

Started. Baseline observed. Ready for Day 2.', tags: ['research'], lastSyncedAt: '2026-05-18T14:30:00Z'}. The server has an older version of note #42 (body: '# Day 1

Started.', lastSaved: '2026-05-18T14:00:00Z').

**Trigger:**

Kohl relaunches the browser. App.tsx mounts and calls loadNote(42). It fetches GET /api/notes/42 and receives {id: 42, title: 'Research Log', body: '# Day 1

Started.', tags: ['research'], updated_at: '2026-05-18T14:00:00Z', revision_id: '7a3f8e...'}. The EditorLayout also checks localStorage and finds the draft. Since localStorage.lastSyncedAt ('2026-05-18T14:30:00Z') > server.updated_at ('2026-05-18T14:00:00Z'), localStorage is newer.

**Expected:**

EditorLayout shows a modal: 'You have unsaved changes from your last session. Your draft: [title and 50-char body preview]. Server version: [title and 50-char body preview]. Would you like to: (a) Restore Draft, (b) Load Server Version, (c) Cancel?' Kohl clicks (a). The editor state is populated from localStorage: title = 'Research Log', body = '# Day 1

Started. Baseline observed. Ready for Day 2.', tags = ['research']. localStorage.lastSyncedAt is NOT cleared (it's not synced yet). The Save button is enabled. When Kohl clicks Save, the PUT request is sent with the localStorage values, the backend writes them, and localStorage is then cleared.

**Concern:**

If Kohl's draft is lost (modal doesn't appear, or is dismissed before she can choose Restore), she loses her unsaved work and sees only the server version. If the modal appears but the text is too small to read, she might accidentally choose 'Load Server Version' and lose the draft. If the draft is restored but the keystroke buffer is cleared immediately (instead of on successful save), Kohl can't retry if the save fails.

**Property:**

Unsaved keystroke buffer survives tab crash and page reload, and user is given explicit control over whether to keep or discard it.

**Implies:**
- localStorage is checked on every mount
- Collision modal appears when localStorage and server versions differ
- localStorage is cleared only after successful save (200 response), not before
