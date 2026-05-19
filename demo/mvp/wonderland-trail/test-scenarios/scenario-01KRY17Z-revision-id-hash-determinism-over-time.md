## Scenario: Revision ID hash is deterministic: same note state always produces same revision_id

**Severity:** silent-wrongness

**Setup:**
Note created with title='Test Note', body='Content here', tags=['research', 'async'], created_at=2026-05-18T17:13:21.000000Z, updated_at=2026-05-18T17:13:21.000000Z.
The note is immediately fetched via GET /notes/1, and the response includes revision_id = 'hash_A'.
The note is saved in a backup at T1.
At T2 (minutes later), the note is fetched again without any edits in between.

**Trigger:**
The second GET /notes/1 at T2 returns the note. The revision_id is computed fresh from the database state.

**Expected:**
The second GET returns revision_id = 'hash_A' (identical to T1). The hash is deterministic: same state always produces same hash.

**Concern:**
If the hash computation includes non-deterministic elements (e.g., random salt, current timestamp, dict iteration order in Python <3.7), the same note state will hash differently on different reads or in different environments. This causes: (1) client sends If-Match with expected hash, server recomputes hash and gets different value, collision detection fails spuriously; (2) client can never save because hashes never match.

**Property:**
For all notes that are not edited, the revision_id computed on multiple reads (GET requests at T1, T2, T3...) is identical.

**Implies:**
- Implies SHA256 hash must be computed from: title, body, sorted_tag_ids (as integers, sorted numerically), updated_at (in fixed ISO8601 format with microseconds, UTC).
- Implies created_at should NOT be included (it never changes, adds no signal).
- Implies the JSON serialization (or string concatenation) before hashing must be deterministic (Python dicts are ordered in 3.7+, but json.dumps() with sort_keys=True is safer).
- Implies test should compute hashes multiple times on the same note and verify they match.

