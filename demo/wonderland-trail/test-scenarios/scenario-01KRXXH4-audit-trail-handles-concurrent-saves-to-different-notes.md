## Scenario: Audit trail handles concurrent saves to different notes

**Severity:** degradation

**Setup:**
Kohl has two notes open in separate browser windows. Window 1 is editing "note A", Window 2 is editing "note B". Both are saving at nearly the same time (within milliseconds of each other).

Window 1 save:
- note_id = 1, title = "async", body = "tokio", revision_id = hash(A)
- audit_log entry written with timestamp = 10:00:00.000123

Window 2 save:
- note_id = 2, title = "python", body = "asyncio", revision_id = hash(B)
- audit_log entry written with timestamp = 10:00:00.000124

**Trigger:**
Both saves complete successfully and return 200 to their respective windows.

**Expected:**
The audit_log has two entries:
- Entry 1: note_id = 1, saved_state = {title: "async", body: "tokio", ...}, timestamp = 10:00:00.000123
- Entry 2: note_id = 2, saved_state = {title: "python", body: "asyncio", ...}, timestamp = 10:00:00.000124

Both notes table rows are updated. No collision. No corruption. Queries on audit_log can retrieve entries by note_id independently.

**Concern:**
Concurrent writes might:
- Interfere with each other (e.g., revision_id from save A overwrites revision_id from save B in a shared variable)
- Cause audit_log entries to be written in the wrong order (timestamps out of order)
- Lose one of the saves entirely (both writes target the same audit_log row, one overwrites the other)
- Violate isolation (save A reads the audit_log while save B is writing, sees partial state)

This would mean the audit trail is unreliable under concurrent load. In production (if multiple users or tabs are common), the audit trail would be silently corrupted.

**Property:**
Concurrent saves to different notes do not interfere with each other. Each save's audit_log entry is independent. The audit_log faithfully reflects all concurrent saves with correct note_ids, saved_states, and timestamps.

**Implies:**
- Requires proper isolation at the database level (e.g., row-level locking, MVCC)
- SQLite uses coarse-grained locking (database-level); concurrent writes may be serialized, but should still be correct
- The implementation must not use shared state (e.g., global revision_id variables) across concurrent requests
- Timestamps must be generated server-side (not client-supplied) to ensure uniqueness
