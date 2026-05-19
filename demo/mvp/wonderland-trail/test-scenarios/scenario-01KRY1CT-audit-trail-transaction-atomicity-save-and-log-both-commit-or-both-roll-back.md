## Scenario 328: Audit trail transaction atomicity—save and log both commit or both roll back

**GUID:** 01KRY1CT9RYR088A6WTPTNAHTA
**Severity:** breakage

**Setup:**

Kohl saves a note. The save endpoint writes to notes table, computes revision_id, and writes to audit_log. Midway through, assume a failure: notes table write succeeds but audit_log write fails (disk full, constraint violation).

**Trigger:**

The save attempt either completes entirely or fails entirely.

**Expected:**

One of two outcomes: (1) Both notes table and audit_log entries are committed (success path), or (2) The transaction rolls back entirely, neither table is modified (failure path). There is no partial state.

**Concern:**

The implementation might not use transaction semantics correctly: writes to notes and audit_log as separate transactions (one commits, the other fails → inconsistent state). Audit_log writes after notes commits with no chance to roll back.

**Property:**

For all note saves: (notes table is updated) ⟺ (audit_log entry is inserted). If either fails, both are rolled back. The operations are atomic from the client's perspective.

**Implies:**
- Requires a single database transaction wrapping both writes
- Rollback logic must be present and tested
- If the database session crashes, the entire transaction is rolled back by the database
- No application-level 'compensating transactions' needed; database transactions are sufficient
