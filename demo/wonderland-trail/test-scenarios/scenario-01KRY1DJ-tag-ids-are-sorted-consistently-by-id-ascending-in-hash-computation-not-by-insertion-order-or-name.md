## Scenario 337: tag_ids are sorted consistently by ID (ascending) in hash computation, not by insertion order or name

**GUID:** 01KRY1DJHRX8TH9EM6XEXWJ9BE
**Severity:** degradation

**Setup:**

Note with tags in insertion order [tag_id=5, tag_id=2, tag_id=8]. When computing revision_id, which sort order is used: by ID ascending [2, 5, 8], by insertion order [5, 2, 8], or by name?

**Trigger:**

(1) Create note with tags [5, 2, 8], save (revision_id='hash_1'). (2) Fetch (ORM may return tags in different order). (3) Save again without modifying (revision_id='hash_2'). (4) Fetch again, save (revision_id='hash_3').

**Expected:**

hash_1 == hash_2 == hash_3. All identical because note state hasn't changed. Hash computation must sort tag_ids by ID internally.

**Concern:**

If implementation sorts by insertion order, same note produces different revision_ids depending on tag order in DB result. False-positive collisions: user re-fetches their own note and tries to save, system thinks it's a collision.

**Property:**

For all notes with same tag set, revision_id is identical regardless of order tags appear in response. Requires explicit sorted(tag_ids) by ID before hashing.

**Implies:**
- Implies code review: verify explicit `sorted(tag_ids)` in hash computation, not implicit reliance on tag order.
- Implies test: create note with tags [5, 2, 8], manually re-order tags in DB to [2, 8, 5], fetch and re-save, verify revision_id unchanged.
