## Scenario 057: Two concurrent POST requests both creating notes with the same tag name hit UNIQUE constraint

**GUID:** 01KRXTD96CAEAJCAJEH0RQWM01
**Severity:** silent-wrongness

**Setup:**

Two concurrent POST /api/notes requests, both with tag_names=['research']. The _associate_tags function queries for the tag by name, and if not found, calls db.add(Tag(name=tag_name)).

**Trigger:**

Both requests execute the query-then-create pattern simultaneously. Both queries find no existing tag. Both call db.add(Tag(name='research')). Both flush/commit.

**Expected:**

SQLite serializes writes at the WAL level. One request acquires the lock, commits successfully. The second request should find the tag created by the first, and both notes are created successfully.

**Concern:**

The code doesn't handle UNIQUE constraint violations from concurrent tag creation. If the second request's flush hits the constraint before seeing the first request's commit, it fails with IntegrityError, the session rolls back, and the endpoint returns 500. The note creation fails — breakage for the user. The current pattern is classic ORM race condition.

**Property:**

For all concurrent requests creating notes with the same tag name T, exactly one tag with name T exists in the database afterward, and all note-creation requests succeed.

**Implies:**
- Implies architectural decision: should tag creation use upsert (INSERT OR IGNORE), or handle IntegrityError and retry, or use a different concurrency pattern? Cat should review the concurrency model and establish a pattern.
