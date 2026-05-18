## Scenario 336: audit_log captures every save attempt, including those rejected for collision

**GUID:** 01KRY1DJHRX8TH9EM6XEXWJ9BD
**Severity:** silent-wrongness

**Setup:**

Note id=42 is saved three times: (1) revision_id='hash_A' (succeeds), (2) revision_id='hash_B' (succeeds), (3) If-Match='hash_A' (collision, rejected).

**Trigger:**

Query SELECT * FROM audit_log WHERE note_id=42 ORDER BY created_at.

**Expected:**

Exactly 3 rows. Row 1: revision_id='hash_A', collision_detected=false. Row 2: revision_id='hash_B', collision_detected=false. Row 3: revision_id='hash_A', collision_detected=true (or foreign key to hash_B). All rows include note_id, operator_id, saved_state, created_at.

**Concern:**

If audit_log only records successful saves, forensic trail is incomplete. Kohl cannot reconstruct what happened to her missing edit. Log says 'two saves succeeded' when actually three attempts were made and one was rejected. Silent wrongness.

**Property:**

For all save attempts (successful or rejected), a row is inserted into audit_log with collision_detected marker reflecting result of If-Match validation.

**Implies:**
- Implies schema: audit_log must include collision_detected column.
- Implies code: PUT endpoint inserts audit_log AFTER validating If-Match, not before.
