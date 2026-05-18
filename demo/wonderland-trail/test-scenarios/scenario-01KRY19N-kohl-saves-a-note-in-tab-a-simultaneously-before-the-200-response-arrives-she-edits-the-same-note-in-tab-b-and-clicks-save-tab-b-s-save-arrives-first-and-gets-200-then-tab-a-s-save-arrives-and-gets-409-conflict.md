## Scenario 261: Kohl saves a note in tab A, simultaneously (before the 200 response arrives) she edits the same note in tab B and clicks Save—tab B's save arrives first and gets 200, then tab A's save arrives and gets 409 Conflict

**GUID:** 01KRY19NJ0GS53FVHNDWBCBT8C
**Severity:** breakage

**Setup:**

Kohl opens the same note in two tabs (accident). Tab A has revision_id 'rev_5' in component state. Tab B also has revision_id 'rev_5'. She clicks Save in both tabs within the same second (before either response arrives). Tab B's request reaches the server first.

**Trigger:**

Tab B's PUT /notes/{id} with revision_id 'rev_5' arrives first. Server processes it, increments the revision_id to 'rev_6', and responds 200 with the new revision_id. Tab A's PUT /notes/{id} with revision_id 'rev_5' arrives second, after the server has already moved to 'rev_6'. The server detects a stale revision_id and responds 409 Conflict with the new state and new revision_id 'rev_6'.

**Expected:**

Tab B receives 200, updates its local revision_id to 'rev_6', shows success message. Tab A receives 409, shows a collision warning modal. The modal displays the backend's newer version and gives Kohl a choice: 'Keep my edits in this tab' or 'Load backend version'. If she chooses 'Keep my edits', the editor retains her local content and marks revision_id as stale (or attempts to save again with the new revision_id). If she chooses 'Load backend version', the editor is refreshed with the backend state and revision_id is updated to 'rev_6'.

**Concern:**

The collision modal could be confusing: which version is which? If Kohl can't see the differences between the two versions, she might accidentally discard work. If the modal doesn't clearly show which tab is which, she might save the wrong version. If the 'Keep my edits' option doesn't actually retry the save, her edits will never persist.

**Property:**

When two tabs attempt to save concurrently, the server must detect the collision (via revision_id mismatch) and respond 409. The client must display the conflict clearly to the user and offer a deterministic choice (keep local, load remote, or manually merge).

**Implies:**
- Implies UX design for collision modal—must clearly distinguish the two versions and show what will be lost.
- Implies that the revision_id protocol is load-bearing for collision detection.
- Implies a retry mechanism: if Kohl chooses 'Keep my edits', the editor needs a way to re-attempt the save with the new revision_id.
