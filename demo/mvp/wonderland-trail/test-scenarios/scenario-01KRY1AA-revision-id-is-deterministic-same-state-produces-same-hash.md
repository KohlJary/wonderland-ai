## Scenario: Revision ID is deterministic — same note state produces the same hash

**Severity:** breakage

**Setup:**

Note with title='Rust async', body='The Send + Sync pattern', tag_ids=[1, 3, 2] (unsorted), updated_at='2025-01-18T14:30:45.123456Z'.

**Trigger:**

Compute the revision_id twice without modifying the note: (1) first call, (2) second call. Use the same in-memory note state both times. Do not re-fetch from database.

**Expected:**

Both calls return the identical revision_id hash. Determinism is non-negotiable: if the same state produces different hashes, collision detection breaks silently.

**Concern:**

If revision_id computation includes randomness (e.g., random padding in the hash input), or if tag_ids are sorted inconsistently (by ID one time, by name another time, by insertion order another time), the same note will produce different revision_ids on different calls. This breaks collision detection in two ways:

- **False-positive collisions:** system blocks saves that shouldn't be blocked (If-Match fails when it should succeed)
- **False-negative collisions:** system allows overwrites that should be blocked (If-Match succeeds when it should fail)

Either way, the system appears to work but users silently lose edits (silent-wrongness).

**Property:**

For all note states N, hash(N) computed at time T1 must equal hash(N) computed at time T2, even if N is fetched from the database between T1 and T2. Determinism must hold across server restarts.

**Implies:**

Implies code review: verify that SHA256 hash is computed with consistently-sorted inputs. Specifically: tag_ids must be sorted ascending by ID (e.g., `sorted(tag_ids)`) before inclusion in the hash, not by insertion order, not by name, not left unsorted.

Implies test implementation: write a test that computes revision_id for the same note 100 times and asserts all 100 hashes are identical.
