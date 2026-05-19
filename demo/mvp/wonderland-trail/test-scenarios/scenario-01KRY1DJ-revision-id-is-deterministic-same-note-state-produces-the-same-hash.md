## Scenario 333: revision_id is deterministic: same note state produces the same hash

**GUID:** 01KRY1DJHRX8TH9EM6XEXWJ9BA
**Severity:** breakage

**Setup:**

Note with title='Rust async', body='The Send + Sync pattern', tag_ids=[1, 3, 2] (unsorted), updated_at='2025-01-18T14:30:45.123456Z'.

**Trigger:**

Compute revision_id twice without modifying the note. Use the same in-memory state both times. Do not re-fetch from database.

**Expected:**

Both calls return the identical revision_id hash.

**Concern:**

If revision_id computation includes randomness or inconsistent sorting of tag_ids, the same note produces different hashes on different calls. This breaks collision detection (false-positive or false-negative collisions). Users silently lose edits.

**Property:**

For all note states N, hash(N) computed at time T1 must equal hash(N) computed at time T2. Determinism must hold across server restarts.

**Implies:**
- Implies code review: verify SHA256 hash uses consistently-sorted inputs. Tag IDs must be sorted ascending by ID before hashing.
- Implies test: compute revision_id 100 times on the same note state and assert all hashes are identical.
