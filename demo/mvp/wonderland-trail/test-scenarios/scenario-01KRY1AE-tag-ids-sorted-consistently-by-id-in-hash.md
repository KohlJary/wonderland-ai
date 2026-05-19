## Scenario: Tag IDs are sorted consistently by ID (ascending) in hash computation, not by insertion order or name

**Severity:** degradation

**Setup:**

Note with tags in insertion order: [tag_id=5 (name='Python'), tag_id=2 (name='Async'), tag_id=8 (name='Rust')].

When computing revision_id, the contract specifies: `revision_id = SHA256(sorted([title, body, sorted_tag_ids, updated_at]))`.

The question: what does "sorted_tag_ids" mean?
- Option A: Sort ascending by tag ID: [2, 5, 8]
- Option B: Sort by insertion order (as they appear in the response): [5, 2, 8]
- Option C: Sort by tag name: ['Async', 'Python', 'Rust'] = [2, 5, 8] (coincidentally same as A in this case)

**Trigger:**

(1) Create the note with tags in insertion order [5, 2, 8]. Save. Revision_id='hash_1'.
(2) Fetch the note. ORM returns tags in some order (could be DB insertion order, could be sorted by ID, could be sorted by name). Note which order it is.
(3) Save the note again without modifying it. Revision_id='hash_2'.
(4) Fetch again. Save again. Revision_id='hash_3'.

If the hash computation uses consistent sorting (by ID), all three revision_ids should be identical.

**Expected:**

hash_1 == hash_2 == hash_3. All three saves produce the same revision_id because the note state hasn't changed. The hash computation must sort tag_ids by ID internally, before hashing, regardless of the order in which tags appear in the database result or response.

**Concern:**

If the implementation sorts by insertion order (natural in ORM iteration without explicit sorting), the same note will produce different revision_ids depending on the order tags were associated. Example:

- Note.tags = [5, 2, 8] after first save
- Note.tags = [2, 5, 8] after fetch (different order due to DB query order)
- Hashing [5, 2, 8] produces hash_X
- Hashing [2, 5, 8] produces hash_Y != hash_X
- Same note state, different revision_ids!

This breaks collision detection:
- **False-positive collisions:** a user re-fetches their own note and tries to save again, the system thinks it's a collision even though only they are editing it.
- **Degradation:** the collision detection appears to work but fails silently on re-saves or concurrent edits on the same note.

**Property:**

For all notes with the same tag set, revision_id is identical regardless of the order in which tags appear in the database response or API response. This requires explicit sorting of tag_ids by ID before hashing.

Formally: for all sets T of tag_ids and all permutations P1, P2 of T:
```
hash(title, body, sorted(P1), updated_at) == hash(title, body, sorted(P2), updated_at)
```

where sorted() means ascending by tag ID.

**Implies:**

Implies code review: in the revision_id computation function, there must be an explicit `sorted(tag_ids)` or equivalent, not implicit reliance on tag order.

Implies test: write a test that (1) creates a note with tags [5, 2, 8], (2) manually re-orders tags in the database to [2, 8, 5], (3) fetches and re-saves the note, and verifies revision_id is unchanged.

Implies documentation: update the contract-note to specify "tag_ids sorted ascending by ID" (not "insertion order" or "by name").
