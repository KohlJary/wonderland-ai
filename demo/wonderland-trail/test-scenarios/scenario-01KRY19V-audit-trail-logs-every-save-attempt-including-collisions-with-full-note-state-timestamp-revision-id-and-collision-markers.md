## Scenario 269: Audit trail logs every save attempt (including collisions) with full note state, timestamp, revision_id, and collision markers

**GUID:** 01KRY19VMP015JW631HNJ74GC3
**Severity:** degradation

**Setup:**

Note #1 has id=1, title='X' body='Y' tags=[T1]. The audit_log table is empty. User saves the note once (success), then attempts to save again with a stale revision_id (collision).

**Trigger:**

Save 1: PUT /notes/1 with current revision, new state {title: A, body: B}. Success. Audit log entry is created. Save 2: PUT /notes/1 with stale revision_id, new state {title: C, body: D}. Collision detected, 409 returned. Audit log entry is created for the failed attempt.

**Expected:**

Audit log has two entries: (1) {note_id: 1, timestamp: T1, saved_state: {title: A, body: B, tags: [T1]}, revision_id: hash1, operator_id: 'kohl', collision_detected: false}. (2) {note_id: 1, timestamp: T2, saved_state: {title: A, body: B, tags: [T1]} (unchanged because save failed), revision_id: hash1 (unchanged), operator_id: 'kohl', collision_detected: true, conflicting_revision_id: <client_revision>}. Both entries are immutable (no update or delete).

**Concern:**

The backend might not log collision attempts, only successful saves. This means if a user claims 'I saved X but it shows Y', we can't see the collision event in the audit trail. Or the audit log might not include the full saved state, only a summary like {note_id, revision_id, timestamp}, making forensic reconstruction impossible. Or the audit log might allow UPDATEs or DELETEs, violating immutability and making the trail untrustworthy.

**Property:**

For every note save (successful or collision-failed) at timestamp T, an audit_log entry exists with (note_id, saved_state, revision_id, collision_detected, operator_id, timestamp). The saved_state is the complete serialized note (title, body, tag_ids) at the moment of the save attempt. The audit_log table has no UPDATE or DELETE permissions (INSERT-only). The entry can be queried to reconstruct the full history of saves for that note.

**Implies:**
- Requires audit_log table schema with immutability enforcement — flag for Tweedledum.
- Requires audit log insertion on both successful saves (200) and collision failures (409) — flag for Tweedledum.
- Requires test coverage that queries the audit log and verifies the complete history of save attempts for a given note.
