## Scenario: Audit log captures every save attempt, including those rejected for collision

**Severity:** silent-wrongness

**Setup:**

Note id=42 is subjected to three save attempts:
1. Create with title='First', revision_id='hash_A' (succeeds, 200)
2. Update to title='Second', revision_id='hash_B' (succeeds, 200)
3. Attempt update with If-Match='hash_A' (collision, 409, rejected)

**Trigger:**

Query SELECT * FROM audit_log WHERE note_id=42 ORDER BY created_at ASC.

**Expected:**

Exactly 3 rows in audit_log:

| id | note_id | revision_id | saved_state | collision_detected | operator_id | created_at |
|----|---------|-------------|-------------|-------------------|------------|------------|
| 1  | 42      | hash_A      | {full JSON} | false or null     | 'kohl'     | T1         |
| 2  | 42      | hash_B      | {full JSON} | false or null     | 'kohl'     | T2         |
| 3  | 42      | hash_A      | {old JSON}  | true or 'hash_B'  | 'kohl'     | T3         |

Row 3 represents the rejected save attempt. It includes:
- The revision_id that was sent in If-Match (hash_A).
- The full state that was *attempted* to be saved (the body from Tab B's PUT request).
- A collision_detected marker: either a boolean=true, or a foreign key to the conflicting revision_id='hash_B', or a string field with the conflicting revision.
- The fact that this row exists at all, with collision marker set, proves the save was attempted and rejected.

**Concern:**

If the audit log only records successful saves and skips rejected attempts, Kohl later asks "where did my edit go?" or "why wasn't my change saved?" and the forensic trail is incomplete. We cannot reconstruct what happened. 

The audit log becomes an oracle of only the wins, not the losses. **Silent wrongness:** the log says "two saves succeeded" when actually three save attempts were made and one was silently rejected by collision detection. The user is left confused about whether her save request was ever received.

Additionally, if the audit log doesn't record the revision_id that was sent (only the one that succeeded), we lose the ability to forensically trace which version the client thought was current.

**Property:**

For all save attempts (successful or rejected due to collision), a row is inserted into audit_log. The row includes:
- note_id
- operator_id
- revision_id: the hash of the state that was being saved (or attempted to be saved)
- saved_state: full JSON representation of the note as it would have been (for rejected saves, this is the attempted state, not the actual server state)
- collision_detected: boolean or foreign key indicating whether the save was rejected due to revision_id mismatch
- created_at: timestamp of the attempt

The audit_log is immutable (no UPDATE, no DELETE, only INSERT).

**Implies:**

Implies schema: audit_log table must include a collision_detected column (boolean, or nullable foreign key to audit_log.id of the conflicting save, or a string field holding the conflicting revision_id).

Implies code: the PUT endpoint must insert the audit_log row AFTER validating If-Match, so that collision_detected reflects the actual result of the validation, not a pre-computed value.

Implies test: write a test that attempts three saves (two succeed, one fails due to collision) and verifies the audit_log has exactly 3 rows with correct collision markers.

Implies observability: Dormouse should monitor audit_log for spikes in collision_detected=true, which would indicate high contention (multiple users / tabs editing the same note concurrently).
