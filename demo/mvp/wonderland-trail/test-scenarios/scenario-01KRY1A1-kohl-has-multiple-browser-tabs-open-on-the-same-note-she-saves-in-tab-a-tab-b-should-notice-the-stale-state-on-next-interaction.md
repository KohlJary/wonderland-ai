## Scenario 285: Kohl has multiple browser tabs open on the same note; she saves in Tab A; Tab B should notice the stale state on next interaction

**GUID:** 01KRY1A1CJG4S1VG4H5J0GAQC0
**Severity:** degradation

**Setup:**

Kohl has note 42 open in Tab A and Tab B (same browser, same localStorage shared). She saves note 42 in Tab A (revision_id becomes 'abc123'). Tab B's in-memory Editor state still has the old revision_id 'old_rev'. Kohl continues typing in Tab B (keystrokes buffer to localStorage, which is now stale relative to Tab A's server state).

**Trigger:**

Kohl clicks Save in Tab B while Tab A's save is still in flight or completed. Tab B sends PATCH /api/notes/42 with If-Match: 'old_rev' header.

**Expected:**

Backend receives Tab B's PATCH request. Server's current revision_id is 'abc123' (from Tab A's save). Server compares If-Match header 'old_rev' to current 'abc123' — they don't match. Server returns 409 Conflict with {error: 'ConflictError', server_revision_id: 'abc123', server_state: {...}}. Tab B's Editor receives 409 and displays collision modal: 'Another browser tab saved changes. Your edits are: [preview]. [Overwrite] [Reload]'. Kohl chooses. No silent data loss.

**Concern:**

If the backend doesn't validate If-Match header, Tab B's stale PATCH silently overwrites Tab A's save. If the frontend doesn't interpret 409 Conflict, Kohl doesn't know her save had an issue. Both are silent-wrongness. The collision detection contract must be end-to-end: client sends revision, server validates, client handles 409.

**Property:**

multi_tab_collision_detection_via_if_match_prevents_last_write_wins_overwrites
