## Scenario 281: Kohl opens the app after editing offline; her keystroke buffer and server state match, no collision

**GUID:** 01KRY1A1CJG4S1VG4H5J0GAQBW
**Severity:** silent-wrongness

**Setup:**

Kohl has edited a note offline in the same browser session. localStorage contains {id: 42, title: 'Research Notes', body: 'Initial draft...', revision_id: 'abc123', lastSyncedAt: '2025-05-18T14:00:00Z'}. Server has the same note at the same revision (verified by prior save). Kohl's browser tab is still open.

**Trigger:**

Kohl navigates away from the editor and back (or refreshes the page). EditorLayout mounts with noteId=42. useEffect calls GET /api/notes/42.

**Expected:**

Backend returns {id: 42, title: 'Research Notes', body: 'Initial draft...', revision_id: 'abc123', ...}. Frontend compares localStorage.revision_id ('abc123') to server.revision_id ('abc123') — they match. Editor silently loads from localStorage (preserving Kohl's unsaved keystroke buffer) without warning. Kohl sees her draft exactly as she left it, ready to continue editing. No collision warning appears.

**Concern:**

If the frontend incorrectly treats matching revisions as 'stale' and loads the server version instead, Kohl loses her keystrokes and is confused. Silent loss of unsaved work is the worst failure mode. The merge logic must be correct: matching revision_id means 'no conflict, safe to use local buffer'.

**Property:**

localstorage_keystroke_buffer_survives_navigation_when_no_collision
