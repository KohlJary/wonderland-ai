## Scenario 324: Audit trail entries are immutable—no update or delete

**GUID:** 01KRY1CT9RYR088A6WTPTNAHT6
**Severity:** breakage

**Setup:**

Kohl saves a note "draft thoughts" with body "initial content". The audit_log now has one entry with saved_state = {title: "draft thoughts", body: "initial content", ...}. Later, an administrator or buggy script attempts to UPDATE or DELETE the audit_log entry.

**Trigger:**

An attempt is made to UPDATE or DELETE the audit_log entry.

**Expected:**

The attempt fails. The audit_log entry remains unchanged. Database constraints prevent modifications: audit_log table has guards preventing UPDATE/DELETE, only INSERT is allowed.

**Concern:**

Audit trail entries might be updatable or deletable, allowing someone to cover up evidence of what was saved. The forensic reconstruction requirement becomes meaningless if the audit log is mutable.

**Property:**

Once an entry is inserted into audit_log, it cannot be modified or deleted by any means (application code, SQL, admin). The only permitted operation on audit_log is INSERT.

**Implies:**
- Database schema must have constraints or application-level guards preventing UPDATE and DELETE on audit_log
- Audit_log should be read-only after initial write
- Forensic tooling should be aware that the audit trail is immutable and can be used as ground truth
