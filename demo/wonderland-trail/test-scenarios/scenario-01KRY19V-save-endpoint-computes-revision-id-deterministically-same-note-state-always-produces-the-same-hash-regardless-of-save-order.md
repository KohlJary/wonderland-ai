## Scenario 268: Save endpoint computes revision_id deterministically: same note state always produces the same hash, regardless of save order

**GUID:** 01KRY19VMP015JW631HNJ74GC2
**Severity:** silent-wrongness

**Setup:**

Note #1 initially has title='X' body='Y' tags=[T1, T2]. Two concurrent save paths: Path A saves at time 1ms with updated_at=2026-05-18T17:13:21.1Z, Path B saves at time 2ms with updated_at=2026-05-18T17:13:21.2Z. Both paths update the note to title='Z' body='W' tags=[T2, T1] (same content, same tags but different order in memory).

**Trigger:**

Path A: PUT /notes/1 with If-Match: <old_revision>, new state {title: Z, body: W, tags: [T1, T2]}. Path B separately: PUT /notes/1 with If-Match: <old_revision>, new state {title: Z, body: W, tags: [T2, T1]}. Both succeed on different instances or one blocks and the other retries.

**Expected:**

The revision_id computation must sort tags consistently (e.g., by ID, not memory order). If Path A saves with updated_at=1ms and Path B retries with updated_at=2ms, they should produce different revision_ids. But if the same exact note state is saved twice (same title, same body, same sorted tag IDs, same updated_at), the revision_id must be identical. This is the determinism property: the client can predict the server's revision_id and use it for optimistic locking.

**Concern:**

The endpoint could compute revision_id by hashing the database row directly without sorting tags, leading to hash(title, body, [T1, T2], ts) ≠ hash(title, body, [T2, T1], ts) for the same logical state. This breaks collision detection because a client retrying the same save will get a different revision_id and think it's a new collision. Or the endpoint could include updated_at in the hash without considering that SQLite's updated_at resolution is only milliseconds, so two saves within milliseconds appear to have the same timestamp and the hash becomes non-deterministic.

**Property:**

For all note states S and all timestamps T, SHA256(sorted([S.title, S.body, sorted(S.tag_ids), T])) is deterministic — calling it twice with the same inputs produces the same output. This is the contract revision_id enforcement.

**Implies:**
- Requires specification of the exact hash algorithm and input order in the contract — flag for Tweedledum to verify against contract-note-01KRY0B8.
- Requires tests that verify: hash([title, body, [T1, T2], ts]) == hash([title, body, [T2, T1], ts]) after sorting.
- Requires tests that verify: two saves of the same note at different wall-clock times produce different revision_ids (because updated_at is part of the hash).
