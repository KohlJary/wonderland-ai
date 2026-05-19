## Scenario 351: Revision ID hash is computed from sorted tag IDs, not tag names, regardless of API response order

**GUID:** 01KRY1DY1PSMHZM094C8W7E46R
**Severity:** silent-wrongness

**Setup:**

Note has tags with id=10 (name='python'), id=11 (name='async'). API response includes tag_ids=[10, 11] and tag_names=['python', 'async'].

**Trigger:**

Client caches tag_ids and computes revision_id. Later, the same tags arrive in API response as tag_ids=[11, 10] (different order).

**Expected:**

Both hash computations produce the same result because hashes are computed from sorted_tag_ids=[10, 11], not API order.

**Concern:**

If hash includes tag_ids in API order (unsorted), same note hashes differently depending on API response order. Spurious 409s.

**Property:**

For notes with multiple tags, revision_id is computed from sorted_tag_ids (not tag_names, not API order).

**Implies:**
- Implies hash computation: SHA256(json.dumps({title, body, tag_ids: sorted(tag_ids), updated_at}, sort_keys=True)).
