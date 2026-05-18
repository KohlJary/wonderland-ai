## Scenario 361: Kohl edits a note from two tabs simultaneously; second tab's Save is rejected with 409 Conflict

**GUID:** 01KRY1F5JJWC63TXB9SQCCBZWG
**Severity:** silent-wrongness

**Setup:**

Kohl has opened the same note ({id: 5}) in two browser tabs. Both tabs loaded the note and cached revision_id='abc123'. In Tab A, she changes the title to 'Updated Title'. In Tab B, she changes the body to 'Updated Body'. Tab A clicks Save first.

**Trigger:**

Tab A sends PATCH /api/notes/5 with {title: 'Updated Title', ...} and If-Match: abc123 header. The backend updates the note and returns 200 with a new revision_id='def456'. Tab B, unaware, attempts to save its changes with PATCH /api/notes/5 and If-Match: abc123 (the stale revision_id it cached).

**Expected:**

The backend compares Tab B's If-Match header (abc123) against the current note's revision_id (def456). They don't match. The backend returns 409 Conflict with response {error: 'ConflictError', server_revision_id: 'def456', server_state: {...full note object with new revision_id...}}. Tab B's save does NOT proceed. The UI shows a collision warning: 'Another tab has saved changes. Your edits: [Tab B's draft]. Server's version: [Tab A's version]. Would you like to: (a) Keep my edits, (b) Load server version?'

**Concern:**

If If-Match validation is not implemented, Tab B overwrites Tab A's changes silently. Kohl loses work. Silent wrongness because the app shows no error — both saves appear to succeed in their respective tabs, but one silently discards the other's changes.

**Property:**

If-Match collision detection prevents silent overwrites
