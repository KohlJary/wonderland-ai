## Scenario 326: Audit trail reconstructs note state at any point in time

**GUID:** 01KRY1CT9RYR088A6WTPTNAHT8
**Severity:** degradation

**Setup:**

Kohl saves a note at timestamps 10:00am, 10:05am, 10:10am with progressively updated content. The audit_log has three entries, one for each save, with timestamps and complete saved_state JSON.

**Trigger:**

A forensic query asks 'what was this note's state at 10:07am?'

**Expected:**

Querying SELECT * FROM audit_log WHERE note_id = X AND timestamp <= '10:07am' ORDER BY timestamp DESC LIMIT 1 returns the entry from 10:05am (most recent save before 10:07am) with the correct saved_state.

**Concern:**

The audit trail might not be queryable to answer 'what was the state at time T?' Saved_state might be truncated or incomplete, timestamps might be absent, or the schema might not support forensic access.

**Property:**

For any time T and any note N saved before T, querying the audit_log returns the exact complete state of N at time T (most recent save before or at T). This query must not require reconstruction logic; the result is available as a single row.

**Implies:**
- Audit trail must use full snapshots (confirmed by ADR-005)
- saved_state field must contain complete note {title, body, tags, timestamps, ...}
- Queries must be efficient: SELECT ... WHERE note_id = N AND timestamp <= T ORDER BY timestamp DESC LIMIT 1
- No reconstruction logic; every row is a standalone, complete state
