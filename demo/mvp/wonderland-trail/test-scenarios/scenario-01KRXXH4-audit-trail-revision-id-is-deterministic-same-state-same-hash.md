## Scenario: Audit trail revision ID is deterministic—same state, same hash

**Severity:** silent-wrongness

**Setup:**
Kohl saves a note with title "experiment v2", body "test results go here", tags: ["research"]. The backend computes revision_id = hash(saved_state_1) and logs it to audit_log. Later, Kohl modifies the note (adds body text), saves it, gets revision_id = hash(saved_state_2). Then she undoes the edit (removes the text she just added), and saves again with title and body matching the first save.

**Trigger:**
The second save (after undo) completes and returns the note with a revision_id.

**Expected:**
The revision_id from the third save matches the revision_id from the first save, because the saved state is identical. The audit_log has three entries: one with hash_1, one with hash_2, one with hash_1 again. The two hash_1 entries have identical saved_state content.

**Concern:**
The revision_id might be non-deterministic (e.g., based on insertion order, wall-clock time, or random salt). If Kohl saves the same note twice, the revision_ids differ even though the content is identical. This means collision detection can't rely on revision_id as a proxy for content equality—the frontend might incorrectly think there's a collision when there isn't, or miss real collisions. Worse: forensic queries like "what was the note on 2026-05-18 at 3pm" might have ambiguous answers if the same state is hashed differently at different times.

**Property:**
For all note states S and all times T1, T2: hash(S) at T1 = hash(S) at T2. Hashing is deterministic and content-dependent only (invariant to insertion order, wall-clock time, random state, etc.).

**Implies:**
- Hashing must be done on a canonical JSON representation (sorted keys, consistent field order, no floating-point precision surprises)
- Hashing must be done at save time, not derived from timestamps or transaction sequence
- Client and server must be able to independently recompute the same hash for validation
