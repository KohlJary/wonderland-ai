## Scenario: Audit trail reconstructs note state at any point in time

**Severity:** degradation

**Setup:**
Kohl saves a note at timestamps:
- 10:00am: title "async", body "tokio", tags ["rust"]
- 10:05am: title "async patterns", body "tokio + channels", tags ["rust", "concurrency"]
- 10:10am: title "async patterns", body "tokio + channels + crossbeam", tags ["rust", "concurrency"]

The audit_log has three entries, one for each save, with timestamps and complete saved_state JSON for each.

**Trigger:**
A forensic query asks "what was this note's state at 10:07am?"

**Expected:**
Querying the audit_log: SELECT * FROM audit_log WHERE note_id = X AND timestamp <= '10:07am' ORDER BY timestamp DESC LIMIT 1 returns the entry from 10:05am (the most recent save before 10:07am). The saved_state field contains {title: "async patterns", body: "tokio + channels", tags: ["rust", "concurrency"]}.

A second query at 10:12am returns the 10:10am entry, with the updated body.

**Concern:**
The audit trail might not be queryable in a way that answers "what was the state at time T?" For instance:
- saved_state might be truncated or incomplete, making reconstruction impossible
- timestamps might be absent or NULL, making temporal queries useless
- The schema might not be designed for forensic access (e.g., no index on note_id + timestamp)
- Without full snapshots (only deltas), reconstructing state at T requires replaying all saves up to T—this is complex and error-prone

The story says "full snapshots, not delta encoding" specifically to avoid this problem. But if the implementation uses deltas anyway, or if snapshots are incomplete, the reconstruction property breaks.

**Property:**
For any time T and any note N that was saved before T, querying the audit_log can return the exact complete state of N at time T (the most recent save before or at T). This query must not require reconstruction logic (replay); the result must be available as a single row.

**Implies:**
- Audit trail must use full snapshots (confirmed by ADR-005)
- saved_state field must contain the complete note {title, body, tags, timestamps, ...}
- Queries must be efficient: SELECT ... WHERE note_id = N AND timestamp <= T ORDER BY timestamp DESC LIMIT 1
- No reconstruction logic; every row is a standalone, complete state
