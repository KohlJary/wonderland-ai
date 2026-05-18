## Scenario: Audit trail logs a complete snapshot on every note save

**Severity:** breakage

**Setup:**
Kohl creates a new note with title "Rust async patterns" and body "tokio::spawn creates a new task". She has no tags on this note. The backend writes the note to the notes table and generates a revision_id (SHA256 hash of the saved state).

**Trigger:**
The save endpoint completes and returns 200 with the note's id and revision_id.

**Expected:**
The audit_log table now contains one entry for this save:
- note_id = <the note's id>
- saved_state = full JSON snapshot: {title: "Rust async patterns", body: "tokio::spawn creates a new task", tag_ids: [], timestamp: <ISO8601>, user_id: "kohl"}
- revision_id = deterministic SHA256 hash of the saved state
- timestamp = server-side ISO8601 (not client-supplied)
- state_hash = same as revision_id (both SHA256 of saved_state)

**Concern:**
The audit trail might not be written (no entry in audit_log), or the entry might be incomplete (missing fields, NULL values, truncated state). This would mean a save occurred but the forensic record is not captured — Kohl could later claim her content was lost but we'd have no evidence of what she saved.

**Property:**
For every successful note save to the notes table, there exists at least one corresponding entry in the audit_log table with the exact saved state and a deterministic revision_id.

**Implies:**
- Requires careful transaction semantics (save must be atomic: note + audit entry both commit or both roll back)
- Requires deterministic hashing (same note state always produces same hash, regardless of insert order or column ordering in JSON)
