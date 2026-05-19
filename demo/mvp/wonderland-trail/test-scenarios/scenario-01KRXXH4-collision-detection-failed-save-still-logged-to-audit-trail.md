## Scenario: Collision detection—failed save still logged to audit trail

**Severity:** silent-wrongness

**Setup:**
Kohl has two browser tabs open editing the same note. Both tabs loaded the note at revision_id = "hash_A" (the current state). Tab B edits the body and saves successfully, generating a new revision_id = "hash_B". The audit_log now has an entry for hash_B. Tab A, unaware of the change, also edits the body (differently) and attempts to save with revision_id = "hash_A" (the stale value it read).

**Trigger:**
Tab A's save request arrives at the backend with revision_id = "hash_A", but the current state is hash_B. The backend detects the collision (revision_ids don't match), rejects the save, and returns 409 Conflict with the current state (hash_B). Tab A's note is NOT written to the notes table (correctly). But what about the audit trail?

**Expected:**
The audit_log contains an entry for this collision attempt. The entry has:
- note_id = <same note>
- saved_state = <the state Tab A tried to save>
- revision_id = <the hash of Tab A's attempted state>
- timestamp = <server time>
- user_id = "kohl"
- conflict_detected = true (or similar marker)
- conflicting_revision_id = "hash_B" (the revision that was already current)

Later, if Kohl investigates "why did my edits disappear?", the audit log shows that:
1. Tab B saved successfully with hash_B
2. Tab A attempted to save a different state with hash_A, but collision was detected (hash_A != hash_B)
3. Tab A's state was never committed to the notes table (by design, to prevent overwrite)

**Concern:**
The audit trail might only log *successful* saves, not collision attempts. If Tab A's collision-rejected save is not logged, the forensic trail is incomplete. Kohl might see "Tab B's save was logged, but Tab A's save is missing" and wonder if data was silently lost. The actual answer is "Tab A tried to overwrite hash_B but we detected the collision and rejected it" — but the log doesn't say that. This is a breakdown of the "complete forensic reconstruction" requirement.

**Property:**
For every save attempt (successful or collision-rejected), there is an audit_log entry with the attempted state. Successful saves have conflict_detected = false (or absent). Collision-detected saves have conflict_detected = true and conflicting_revision_id recorded.

**Implies:**
- Audit trail must log even failed saves (collision attempts)
- Collision metadata must be attached to the log entry (conflict_detected flag, conflicting_revision_id)
- Forensic queries can now answer "why didn't my save work?" by looking for conflict_detected entries
