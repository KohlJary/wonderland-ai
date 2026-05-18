## Scenario 366: Kohl clicks Save after a keystroke pause; backend note is unchanged since her last sync; Save succeeds and she sees 'Saved' confirmation

**GUID:** 01KRY1G5562S7JSHVEXACBHXDW
**Severity:** silent-wrongness

**Setup:**

Kohl has opened note #42 (title: 'Research Log', body: '# Day 1

Started the experiment.', tags: ['research', 'live']). The editor loaded it from backend and cached revision_id = '7a3f8e...' (SHA256 of the saved state). She has been typing for 30 seconds. No other tabs have this note open.

**Trigger:**

Kohl pauses typing, clicks the Save button. The editor POSTs {title: 'Research Log', body: '# Day 1

Started the experiment. Observed baseline behavior.', tags: ['research', 'live'], revision_id: '7a3f8e...'}

**Expected:**

Backend receives the PUT, compares revision_id '7a3f8e...' against the note's current revision. They match. Backend writes the updated body to SQLite in a single transaction, computes the new revision_id (SHA256 of the new state), and responds 200 with {id: 42, title: '...', body: '...', revision_id: 'a2c4d9...', ...}. Frontend clears localStorage, updates the cached revision_id to 'a2c4d9...', and displays a brief 'Saved' message for 1-2 seconds. The UI remains enabled for further edits.

**Concern:**

Kohl's core workflow is Save → see confirmation → continue or close. If the save silently fails and returns 200 with a different revision_id without displaying feedback, or if the browser doesn't update the cached revision_id, the next Save could falsely detect a collision even though there was no collision. This is silent data loss of the save event (Kohl thinks her changes persisted, but they didn't).

**Property:**

Save succeeds atomically and Kohl receives synchronous feedback that the save completed.

**Implies:**
- Atomic transaction: title, body, tags all persist or all roll back
- Deterministic revision_id: same note state always hashes to the same value
- Response includes new revision_id so frontend can track it
- localStorage cleared after successful save so stale state doesn't trigger false collision on next open
