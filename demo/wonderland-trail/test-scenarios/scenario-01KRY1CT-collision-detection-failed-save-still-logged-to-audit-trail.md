## Scenario 325: Collision detection—failed save still logged to audit trail

**GUID:** 01KRY1CT9RYR088A6WTPTNAHT7
**Severity:** silent-wrongness

**Setup:**

Kohl has two browser tabs open editing the same note. Both loaded at revision_id = "hash_A" (current state). Tab B edits and saves successfully, generating revision_id = "hash_B". Tab A edits differently and attempts to save with stale revision_id = "hash_A".

**Trigger:**

Tab A's save request arrives with revision_id = "hash_A", but current state is hash_B. The backend detects collision, rejects the save, and returns 409 Conflict.

**Expected:**

The audit_log contains an entry for this collision attempt with saved_state = (what Tab A tried to save), conflict_detected = true, and conflicting_revision_id = "hash_B".

**Concern:**

The audit trail might only log successful saves, not collision attempts. The forensic trail is incomplete—we don't see Tab A's collision-rejected save, so the investigation is inconclusive.

**Property:**

For every save attempt (successful or collision-rejected), there is an audit_log entry with the attempted state. Successful saves have conflict_detected = false. Collision-detected saves have conflict_detected = true and conflicting_revision_id recorded.

**Implies:**
- Audit trail must log even failed saves (collision attempts)
- Collision metadata must be attached to the log entry (conflict_detected flag, conflicting_revision_id)
- Forensic queries can answer 'why didn't my save work?' by looking for conflict_detected entries
