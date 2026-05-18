## Scenario 329: Audit trail handles concurrent saves to different notes

**GUID:** 01KRY1CT9RYR088A6WTPTNAHTB
**Severity:** degradation

**Setup:**

Kohl has two notes open. Window 1 saves "note A" with revision_id = hash(A). Window 2 saves "note B" with revision_id = hash(B). Both save nearly simultaneously.

**Trigger:**

Both saves complete successfully within milliseconds of each other.

**Expected:**

The audit_log has two entries: one for note_id=1 with saved_state=A, one for note_id=2 with saved_state=B. Both notes table rows are updated. No collision. No corruption.

**Concern:**

Concurrent writes might interfere (revision_id from save A overwrites save B), cause entries to be written in wrong order, lose one save entirely, or violate isolation. The audit trail would be corrupted under concurrent load.

**Property:**

Concurrent saves to different notes do not interfere with each other. Each save's audit_log entry is independent. The audit_log faithfully reflects all concurrent saves with correct note_ids, saved_states, and timestamps.

**Implies:**
- Requires proper isolation at the database level (row-level locking, MVCC)
- The implementation must not use shared state across concurrent requests
- Timestamps must be generated server-side to ensure uniqueness
