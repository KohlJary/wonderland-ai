## Scenario 367: Kohl has two editor tabs open for the same note. Tab A saves. Tab B tries to save with stale revision_id. Tab B sees 'Another tab updated this note' and can choose to reload or overwrite.

**GUID:** 01KRY1G5562S7JSHVEXACBHXDX
**Severity:** silent-wrongness

**Setup:**

Kohl opened note #42 in two browser tabs (both logged in as her, same device, same note). Tab A and Tab B both fetched the note at the same time and both cached revision_id = '7a3f8e...'. Tab A: Kohl edits the body and clicks Save. Tab B: Kohl independently edits the body to a different text. Both editors show their local text and are ready to save.

**Trigger:**

Tab A's Save completes successfully. Backend computes new revision_id for the Tab A version: '9xk5m1...'. Tab B, unaware of Tab A's save, clicks Save. It sends PUT with revision_id: '7a3f8e...' (the stale value cached before Tab A's save).

**Expected:**

Backend receives Tab B's PUT. It compares the If-Match header (Tab B's '7a3f8e...') against the note's current revision_id (Tab A's '9xk5m1...'). They don't match. Backend DOES NOT write Tab B's changes to the database. Instead, it responds 409 Conflict with response body {error: 'ConflictError', detail: 'This note was updated by another client', server_revision_id: '9xk5m1...', server_state: {id: 42, title: '...', body: '<Tab A's version>', tags: [...], revision_id: '9xk5m1...'}}. Frontend receives 409, shows a modal: 'This note was updated in another tab. Your unsaved changes are [preview]. Would you like to: (a) Keep my changes (overwrite), (b) Load the other tab's version, (c) Cancel?' Kohl chooses (a), and Tab B re-sends the PUT with the updated revision_id from the 409 response. Or Kohl chooses (b), Tab B reloads the note with the server version.

**Concern:**

Without collision detection, the second tab's Save would silently overwrite the first tab's changes, and Kohl would lose work. With collision detection, Kohl is given explicit control over which version to keep. This is critical for a researcher who might be experimenting with different edits across tabs and needs to know which one wins.

**Property:**

Collision detection prevents silent data loss when multiple tabs edit the same note concurrently.

**Implies:**
- If-Match header required on PUT requests (the client must send its cached revision_id)
- 409 response includes server's current revision_id and full note state so client can decide
- 409 is retryable: client can re-send PUT with updated revision_id after user chooses to overwrite
