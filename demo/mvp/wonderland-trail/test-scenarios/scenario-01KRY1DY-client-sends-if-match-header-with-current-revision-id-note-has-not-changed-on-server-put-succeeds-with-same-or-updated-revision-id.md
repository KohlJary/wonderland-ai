## Scenario 346: Client sends If-Match header with current revision_id, note has not changed on server, PUT succeeds with same or updated revision_id

**GUID:** 01KRY1DY1PSMHZM094C8W7E46K
**Severity:** breakage

**Setup:**

Note id=1, title='test', body='hello', tags=['a'] (id=10), updated_at=2026-05-18T17:13:21Z. Backend computes revision_id='hash_A' (SHA256(sorted([test, hello, [10], updated_at]))). Client loads note, caches revision_id='hash_A'.

**Trigger:**

Client sends PUT /notes/1 with If-Match: hash_A, request body {title: 'test', body: 'hello', tag_names: ['a']}. No actual changes.

**Expected:**

PUT returns 200 with updated note. revision_id should be identical to hash_A (no change to any field that affects the hash). If any field actually changed (e.g., title), the new revision_id reflects the new state.

**Concern:**

The most basic scenario. If PUT with matching If-Match fails, collision detection is broken at its core.

**Property:**

For all PUT requests where the request state matches the current server state (no actual edit), the update succeeds with 200.
