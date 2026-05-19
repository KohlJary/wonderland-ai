## Scenario 358: Two browser tabs save the same note concurrently with different states; the first save succeeds with revision_id=hash1, the second save detects collision (revision_id mismatch) and returns 409; both saves are logged to audit_trail

**GUID:** 01KRY1EAP8DPXCMJPQSNAEYA5X
**Severity:** breakage

**Setup:**

Kohl has two editor tabs open on the same note (id=42, revision_id='hash1' at load time). Tab A edits title to 'Updated A' and clicks Save. Tab B edits body to 'Updated B' and clicks Save. Tab A completes first (saves 'Updated A'), server assigns revision_id='hash2'. Tab B then sends If-Match: 'hash1' but server has 'hash2'.

**Trigger:**

Tab B Save request is processed.

**Expected:**

Tab B receives HTTP 409 Conflict with {error: 'ConflictError', server_revision_id: 'hash2', server_state: {...}}. Two audit_log entries exist: entry for Tab A's successful save (saved_state='Updated A', revision_id='hash2', collision_detected=false). Entry for Tab B's failed attempt (saved_state='Updated B', revision_id='hash1', collision_detected=true, conflicting_revision_id='hash2'). Tab B's entry is immutably logged as a collision attempt.

**Concern:**

If the collision is not logged to audit_trail, the system has no forensic record that Tab B tried to overwrite Tab A's change. If collision_detected is not set to true, reconstructing the conflict history is impossible. If the Tab B entry is not created at all, audit trail is incomplete.

**Property:**

Audit trail logs both successful saves and failed (collision) saves; collision_detected flag is set accurately; conflicting_revision_id is captured; both entries are queryable and immutable

**Implies:**
- collision detection must happen before the save, so if-match check must be logged whether it passes or fails
- failed save should not update the note, but audit entry should still be created
