## Scenario: Revision ID hash is computed from sorted tag IDs, not tag names, ensuring consistency across serialization

**Severity:** silent-wrongness

**Setup:**
Note has two tags: id=10 (name='python'), id=11 (name='async'). API response includes both tag_ids=[10, 11] and tag_names=['python', 'async'].
Revision hash is computed from: sorted([title, body, sorted([10, 11]), updated_at]) = SHA256(...).

**Trigger:**
Client loads note, sees tag_ids=[10, 11], tag_names=['python', 'async']. Client caches tag data. Client computes revision_id locally using tag_ids.
Later, the same tags are fetched and the API response could return them in any order: tag_ids=[11, 10], tag_names=['async', 'python'].
Client computes revision_id from tag_ids=[11, 10] (unsorted).

**Expected:**
Both hashes should be identical because the hash is computed from sorted_tag_ids. Whether the API returns [10, 11] or [11, 10], the hash is always sorted before hashing: SHA256([..., sorted([10, 11])]).

**Concern:**
If the hash includes tag_names instead of tag_ids, or if tag_ids are not sorted before hashing, then: (1) API response order variations cause hash divergence; (2) same note state hashes differently depending on how the API serialized the tags; (3) spurious 409 Conflict errors.

**Property:**
For all notes with multiple tags, the revision_id hash is computed from sorted_tag_ids (not tag_names, not API order). Same logical state always produces same hash regardless of API response order.

**Implies:**
- Implies backend hash computation: revision_id = SHA256(json.dumps({title, body, tag_ids: sorted(tag_ids), updated_at}, sort_keys=True)).
- Implies tag_ids are integers, sorted numerically before hashing.
- Implies test should verify that notes with tags in different orders produce same revision_id.

