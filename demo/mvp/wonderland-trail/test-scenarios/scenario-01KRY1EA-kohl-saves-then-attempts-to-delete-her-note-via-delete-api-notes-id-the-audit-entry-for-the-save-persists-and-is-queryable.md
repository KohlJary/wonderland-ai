## Scenario 356: Kohl saves, then attempts to delete her note via DELETE /api/notes/{id}; the audit entry for the save persists and is queryable

**GUID:** 01KRY1EAP8DPXCMJPQSNAEYA5V
**Severity:** degradation

**Setup:**

Kohl has saved a note (audit entry exists). She then requests note deletion.

**Trigger:**

DELETE /api/notes/{id} succeeds (204 No Content).

**Expected:**

The note is removed from the notes table (soft-delete or hard-delete per ticket design). The audit_log entry from the prior save remains in audit_log, immutable and queryable. A query SELECT * FROM audit_log WHERE note_id={id} returns the prior audit entry. Kohl can retrieve the historical state of the deleted note from the audit log.

**Concern:**

If the audit_log entry is deleted when the note is deleted (cascade delete), the audit trail is incomplete and Kohl loses the record of what she saved. If the entry is locked/immutable but becomes inaccessible due to FK constraint, it's technically present but not useful.

**Property:**

audit_log entries persist after note deletion; no cascade delete on audit_log; entries remain queryable by note_id even if the note no longer exists

**Implies:**
- Audit log must not have a CASCADE DELETE on the notes FK
- Audit log should have ON DELETE SET NULL or be explicitly left orphaned to preserve historical record
