## Scenario 350: Revision ID is deterministic: same note state always produces the same hash on repeated reads

**GUID:** 01KRY1DY1PSMHZM094C8W7E46Q
**Severity:** silent-wrongness

**Setup:**

Note created with title='Test', body='Content', tags=['research', 'async']. GET /notes/1 returns revision_id='hash_A'.

**Trigger:**

Without editing, GET /notes/1 again. Backend recomputes revision_id from the database state.

**Expected:**

Second GET returns revision_id='hash_A', identical to the first. Same state always hashes to same value.

**Concern:**

If hash computation is non-deterministic (e.g., includes random salt, current timestamp, or dict iteration order), same note will hash differently on different reads. Client If-Match headers will never match, causing spurious 409s.

**Property:**

For all unmodified notes, revision_id computed on multiple GET requests is identical.

**Implies:**
- Implies SHA256 hash must be computed from: title, body, sorted_tag_ids (as integers), updated_at (in fixed ISO8601 format).
- Implies created_at should NOT be included in hash (it never changes).
- Implies JSON serialization must be deterministic (sort_keys=True).
