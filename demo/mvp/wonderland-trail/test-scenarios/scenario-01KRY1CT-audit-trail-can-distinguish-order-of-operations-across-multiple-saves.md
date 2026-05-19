## Scenario 332: Audit trail can distinguish order of operations across multiple saves

**GUID:** 01KRY1CT9RYR088A6WTPTNAHTE
**Severity:** degradation

**Setup:**

Kohl saves the same note three times in rapid succession at 10:00:00, 10:00:01, 10:00:02 with progressively updated content. Each save generates an audit_log entry with revision_id, timestamp, and saved_state.

**Trigger:**

After all three saves complete, a forensic query retrieves the audit_log entries.

**Expected:**

The audit_log has three entries ordered by timestamp. An external tool can reconstruct the timeline unambiguously: v1 first, then v2 (body updated), then v3 (body and tag updated).

**Concern:**

The audit trail might have incorrect/NULL timestamps, store entries out of order, fail to distinguish which save came before which, or use client-supplied time (unreliable). The forensic trail is broken—we can't answer 'when did this happen?'

**Property:**

For any two saves to the same note with timestamps T1 < T2, the audit_log entries have timestamp_1 < timestamp_2. All entries are retrievable in timestamp order. A query SELECT * FROM audit_log WHERE note_id = X ORDER BY timestamp ASC returns entries in save order.

**Implies:**
- Timestamps must be generated server-side (not client-supplied), ensuring NTP-aligned clocks
- Timestamps must be stored with sufficient precision (microseconds or better)
- The audit_log table must have an index on (note_id, timestamp) for efficient temporal queries
