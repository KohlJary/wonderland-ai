## Scenario: Revision ID changes when any of [title, body, tag_ids] change, and is stable on read

**Severity:** degradation

**Setup:**

Note with:
- title='Rust'
- body='async/await patterns'
- tag_ids=[1, 3]
- updated_at='2025-01-18T14:30:00.000000Z'
- revision_id='hash_A' (computed on creation)

**Trigger:**

Perform a sequence of operations:

1. **Fetch the note** (no modifications)
   - Expected revision_id: still 'hash_A'

2. **Update body** to 'async/await patterns with examples'
   - Expected revision_id: new hash, call it 'hash_B'

3. **Update title** to 'Rust Async'
   - Expected revision_id: new hash, call it 'hash_C'

4. **Update tag_ids** to [1, 3, 5] (add tag 5)
   - Expected revision_id: new hash, call it 'hash_D'

5. **Fetch the note again** (no modifications)
   - Expected revision_id: still 'hash_D'

6. **Update created_at** (if possible; server should reject, but test the edge)
   - Expected revision_id: should NOT change (created_at is immutable and not part of hash)

7. **Update updated_at** (happens automatically on save)
   - Expected revision_id: changes, because updated_at is part of the hash input

**Expected:**

- hash_A, hash_B, hash_C, hash_D are all distinct.
- Reading (step 1, 5) does not trigger a new hash computation; revision_id is stable.
- Modifying title, body, or tag_ids always changes revision_id.
- Modifying created_at does NOT change revision_id (created_at is immutable).
- Modifying updated_at (via a save operation) always changes revision_id.

**Concern:**

If revision_id is computed from the wrong fields:
- **Including created_at:** the hash changes on every update (even if content didn't change), breaking collision detection.
- **Excluding title, body, or tag_ids:** changes to those fields don't produce new hashes, so collisions go undetected.
- **Re-computed on every read:** the same note appears to change every time you fetch it, breaking collision detection entirely (every save would be a collision if you re-fetch the note before saving).

Example of a subtle bug: if the hash includes a nanosecond-precision timestamp that changes on every fetch, then:
- Tab A fetches (revision_id='hash_A_with_timestamp_T1')
- Tab A saves (produces 'hash_A_with_timestamp_T2')
- Tab B fetches (revision_id='hash_B_with_timestamp_T3')
- Tab B tries to save with If-Match=hash_B_with_T3
- Server has 'hash_A_with_T2', doesn't match, false collision!

**Property:**

revision_id(note) is a **pure function** of exactly these fields: [title, body, sorted_tag_ids, updated_at].

- If any of these four fields change, revision_id MUST change.
- If none of these four fields change, revision_id MUST stay the same.
- No other fields (id, created_at, or any other column) are included in the hash.
- revision_id is computed on write, not on every read. Reads return the previously-computed revision_id from storage (if stored) or re-compute it if needed, but must produce the same value.

**Implies:**

Implies code: document which fields are included in the revision_id hash. Explicitly list the four: title, body, tag_ids (sorted), updated_at.

Implies code review: verify that the hash function does not include any other fields (especially not created_at, id, or a random value).

Implies test: write parametrized tests that modify each field individually and verify revision_id changes appropriately.
