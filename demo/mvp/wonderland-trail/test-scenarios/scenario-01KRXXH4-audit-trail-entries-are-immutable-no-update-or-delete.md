## Scenario: Audit trail entries are immutable—no update or delete

**Severity:** breakage

**Setup:**
Kohl saves a note "draft thoughts" with body "initial content". The audit_log now has one entry with saved_state = {title: "draft thoughts", body: "initial content", ...}. Later, Kohl's note gets corrupted or accidentally modified by a bug in the backend code.

**Trigger:**
An administrator (or a buggy script, or a manual database edit) attempts to UPDATE the audit_log entry to change the saved_state or DELETE the entry entirely.

**Expected:**
The attempt fails. The audit_log entry remains unchanged. Database constraints prevent modifications:
- audit_log table has a primary key on id; updates to other columns are rejected at the application level (no UPDATE allowed on audit_log)
- Deletion of audit_log entries is not permitted (either via database constraint, application check, or both)

**Concern:**
Audit trail entries might be updatable or deletable, allowing someone to cover up evidence of what was saved (the "forensic reconstruction" requirement becomes meaningless if the audit log is mutable). This is a compliance and audit risk—the Queen's ruling requires the audit trail to be immutable.

**Property:**
Once an entry is inserted into audit_log, it cannot be modified or deleted by any means (application code, SQL, admin). The only permitted operation on audit_log is INSERT.

**Implies:**
- Database schema must have constraints or application-level guards preventing UPDATE and DELETE on audit_log
- Audit_log should be read-only after initial write
- Forensic tooling should be aware that the audit trail is immutable and can be used as ground truth
