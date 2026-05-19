## Scenario: Audit trail transaction atomicity—save and log both commit or both roll back

**Severity:** breakage

**Setup:**
Kohl saves a note "experiment v1" with body "results". The save endpoint:
1. Writes to notes table (title, body, tags updated)
2. Computes revision_id = hash(saved_state)
3. Writes to audit_log table (saved_state, revision_id, timestamp, etc.)
4. Commits the transaction

Midway through, assume a failure: the notes table write succeeds, but the audit_log write fails (e.g., disk full, constraint violation). The transaction is in a partial state.

**Trigger:**
The save attempt either completes (both writes commit) or fails (both writes roll back). There is no partial state.

**Expected:**
One of two outcomes:
- **Success path:** Both notes table and audit_log entries are committed. Kohl sees the note updated and saved. The audit trail is complete.
- **Failure path:** The transaction rolls back entirely. Neither notes table nor audit_log is modified. Kohl sees an error (500 or 503) and the note is not saved.

There is no third outcome where notes table is updated but audit_log is not (or vice versa).

**Concern:**
The implementation might not use transaction semantics correctly:
- Writes to notes table and audit_log as separate transactions (notes commits, but audit_log fails → inconsistent state)
- No rollback logic on failure (notes table updated, but error before audit_log write → missing audit entry)
- Audit_log writes after notes table commits (no chance to roll back if audit_log fails)

If this happens, the audit trail is incomplete: the note was saved but not logged. Kohl can later claim "I had content X" and we have the note but no audit proof of what was saved—the forensic requirement breaks.

**Property:**
For all note saves: (notes table is updated) ⟺ (audit_log entry is inserted). If either fails, both are rolled back. The operations are atomic from the client's perspective (save succeeds if and only if both updates are committed).

**Implies:**
- Requires a single database transaction wrapping both writes
- Rollback logic must be present and tested
- If the database session crashes or times out, the entire transaction is rolled back by the database
- No application-level "compensating transactions" needed; database transactions are sufficient
