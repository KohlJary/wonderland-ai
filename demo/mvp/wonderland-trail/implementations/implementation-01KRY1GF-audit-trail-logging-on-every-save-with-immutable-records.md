## Implementation 058: Audit trail logging on every save with immutable records

**GUID:** 01KRY1GF4D9GTNN9THH5QEXBP3
**Side:** backend
**Ticket:** audit-trail-logging-on-every-save-with-immutable-records
**Contract:** audit-log/v1 — immutable; id (PK), note_id (FK CASCADE), timestamp (server UTC), user_id (nullable), saved_state_json (JSON), revision_id (str 64), state_hash (str 64), collision_detected (bool), conflicting_revision_id (str 64 nullable). Logged after success or 409. No modifications.
**Ready for review:** yes

**Approach:**

AuditLog model: note_id (FK), timestamp (server-assigned UTC), user_id (NULL in v1), saved_state_json ({title, body, tag_ids}), revision_id (SHA256), state_hash (SHA256), collision_detected (bool), conflicting_revision_id (nullable). _record_audit_log() called after every save. On If-Match mismatch: audit entry created with collision_detected=true before returning 409. Append-only schema.

**Invariants Enforced:**
- Audit log rows immutable (append-only)
- saved_state_json is full snapshot
- revision_id deterministic from title + body + sorted(tag_ids) + updated_at
- state_hash provides tamper detection
- collision_detected=true only when 409; conflicting_revision_id then set to server revision
- Timestamps server-assigned, never modified
- Every save (success or collision) = exactly one audit entry

**Schema Changes:**

Added audit_log table: id, note_id (FK CASCADE), timestamp (server-assigned), user_id (nullable), saved_state_json, revision_id, state_hash, collision_detected (bool default false), conflicting_revision_id (nullable). Reversible.

**Failure Modes Handled:**
- Success: collision_detected=false, conflicting_revision_id=NULL
- 409 Conflict: audit log entry created first with collision_detected=true and conflicting_revision_id=server's current revision, then 409 returned
- Database failure: AuditLog write failure rolls back transaction (atomic with note update)

**Files:**
- src/backend/models.py: AuditLog class, compute_revision_id() helper, Boolean import
- src/backend/api/notes.py: _record_audit_log(), If-Match header, collision detection
