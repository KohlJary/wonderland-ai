## Scenario 282: Kohl opens the app after another tab saved changes; her keystroke buffer is stale relative to server

**GUID:** 01KRY1A1CJG4S1VG4H5J0GAQBX
**Severity:** silent-wrongness

**Setup:**

Kohl edited note 42 in Tab A and saved (revision_id changed to 'def456'). She then opened note 42 in Tab B (different browser tab), typed more keystrokes into localStorage (buffer still has old revision_id 'abc123'), but did not save. Now she navigates back to Tab B or refreshes.

**Trigger:**

EditorLayout mounts with noteId=42. useEffect calls GET /api/notes/42.

**Expected:**

Backend returns {id: 42, ..., revision_id: 'def456'}. Frontend compares localStorage.revision_id ('abc123') to server.revision_id ('def456') — they differ. Frontend displays collision warning: 'Your draft differs from the saved version. [Restore Draft] [Load Latest]'. Kohl chooses: 'Restore Draft' keeps her Tab B edits; 'Load Latest' discards them and loads server state. Either way, Kohl is informed of the conflict and can choose.

**Concern:**

If the frontend silently loads the server version without warning, Kohl loses her Tab B edits without knowing. If the frontend silently keeps the buffer without warning, Kohl doesn't realize her edits are based on stale server state. Either silent choice is wrong. The frontend MUST surface the collision decision to Kohl.

**Property:**

collision_detection_on_page_reload_prevents_silent_data_loss
