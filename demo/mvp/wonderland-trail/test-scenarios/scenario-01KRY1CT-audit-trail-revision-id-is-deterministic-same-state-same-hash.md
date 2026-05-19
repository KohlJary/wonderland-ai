## Scenario 323: Audit trail revision ID is deterministic—same state, same hash

**GUID:** 01KRY1CT9RYR088A6WTPTNAHT5
**Severity:** silent-wrongness

**Setup:**

Kohl saves a note with title "experiment v2", body "test results go here", tags: ["research"]. The backend computes revision_id = hash(saved_state_1) and logs it. Later she modifies and saves (revision_id = hash(saved_state_2)), then undoes the edit and saves again with identical content to the first save.

**Trigger:**

The second save (after undo) completes and returns the note with a revision_id.

**Expected:**

The revision_id from the third save matches the revision_id from the first save, because the saved state is identical. The audit_log has three entries: one with hash_1, one with hash_2, one with hash_1 again.

**Concern:**

The revision_id might be non-deterministic (based on insertion order, wall-clock time, or random salt). If Kohl saves the same note twice, the revision_ids differ even though the content is identical. Collision detection can't rely on revision_id as a proxy for content equality.

**Property:**

For all note states S and all times T1, T2: hash(S) at T1 = hash(S) at T2. Hashing is deterministic and content-dependent only (invariant to insertion order, wall-clock time, random state).

**Implies:**
- Hashing must be done on a canonical JSON representation (sorted keys, consistent field order)
- Hashing must be done at save time, not derived from timestamps or transaction sequence
- Client and server must be able to independently recompute the same hash for validation
