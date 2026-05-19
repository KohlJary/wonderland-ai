## Scenario: Audit trail can distinguish order of operations across multiple saves

**Severity:** degradation

**Setup:**
Kohl saves the same note three times in rapid succession:

1. 10:00:00 - Save v1: title="async", body="tokio", tags=["rust"]
2. 10:00:01 - Save v2: title="async-io", body="tokio + crossbeam", tags=["rust", "concurrency"]
3. 10:00:02 - Save v3: title="async-io", body="tokio + crossbeam + rayon", tags=["rust", "concurrency", "parallelism"]

Each save generates an audit_log entry with:
- revision_id = hash(saved_state)
- timestamp = server time (10:00:00, 10:00:01, 10:00:02)
- saved_state = full snapshot

**Trigger:**
After all three saves complete, a forensic query retrieves the audit_log entries for this note.

**Expected:**
The audit_log has three entries, ordered by timestamp:
1. revision_1 = hash(...v1...), timestamp = 10:00:00, saved_state = v1 content
2. revision_2 = hash(...v2...), timestamp = 10:00:01, saved_state = v2 content
3. revision_3 = hash(...v3...), timestamp = 10:00:02, saved_state = v3 content

An external tool can reconstruct the timeline: v1 was saved first, then v2 (body was updated), then v3 (body updated again and tag added). The order is unambiguous.

**Concern:**
The audit trail might:
- Have incorrect or NULL timestamps, making ordering ambiguous
- Store revision_ids in a non-deterministic order (entries inserted out of timestamp order)
- Fail to track which save came before which (no way to distinguish v2 before v3 vs v3 before v2)
- Use wall-clock time from the client instead of server time (client clocks can be wrong or skewed)

If the audit trail can't distinguish order, the forensic trail is broken. Kohl might ask "did I add the parallelism tag in the third save or the second?" and the audit log won't say—it might show the saves out of order, or with identical timestamps.

**Property:**
For any two saves to the same note with timestamps T1 < T2, the audit_log entries have:
- timestamp_1 < timestamp_2 (server-generated timestamps preserve order)
- All entries are retrievable in timestamp order (no reordering)
- A query `SELECT * FROM audit_log WHERE note_id = X ORDER BY timestamp ASC` returns entries in save order

**Implies:**
- Timestamps must be generated server-side (not client-supplied), ensuring NTP-aligned clocks
- Timestamps must be stored with sufficient precision (microseconds or better) to distinguish rapid saves
- The audit_log table must have a primary key and index on (note_id, timestamp) for efficient temporal queries
