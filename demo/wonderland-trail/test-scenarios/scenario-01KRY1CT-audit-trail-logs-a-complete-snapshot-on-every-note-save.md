## Scenario 322: Audit trail logs a complete snapshot on every note save

**GUID:** 01KRY1CT9RYR088A6WTPTNAHT4
**Severity:** breakage

**Setup:**

Kohl creates a new note with title "Rust async patterns" and body "tokio::spawn creates a new task". She has no tags on this note. The backend writes the note to the notes table and generates a revision_id (SHA256 hash of the saved state).

**Trigger:**

The save endpoint completes and returns 200 with the note's id and revision_id.

**Expected:**

The audit_log table now contains one entry for this save with note_id, complete saved_state JSON, revision_id (SHA256 hash), timestamp, and user_id.

**Concern:**

The audit trail might not be written at all, or the entry might be incomplete (missing fields, NULL values, truncated state). This means a save occurred but the forensic record is not captured.

**Property:**

For every successful note save to the notes table, there exists at least one corresponding entry in the audit_log table with the exact saved state and a deterministic revision_id.

**Implies:**
- Requires careful transaction semantics (save must be atomic: note + audit entry both commit or both roll back)
- Requires deterministic hashing (same note state always produces same hash, regardless of insert order)
