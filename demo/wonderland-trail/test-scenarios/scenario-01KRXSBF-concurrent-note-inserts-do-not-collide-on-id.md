## Scenario 004: Concurrent Note inserts do not collide on ID

**GUID:** 01KRXSBF5S803EBBPVQ3MVFZ1M
**Severity:** degradation

**Setup:**

Note table exists; SQLite threadpool is active (as in FastAPI production)

**Trigger:**

Two concurrent requests both insert a Note at the same millisecond

**Expected:**

Both inserts succeed; both rows have unique auto-incremented IDs

**Concern:**

SQLite's autoincrement is row-locked, but under high concurrency in FastAPI's thread pool, lock contention can cause deadlocks or constraint violations. The second insert might fail with 'unique constraint violation' on the ID column. This is degradation, not breakage, because it's a transient edge case, not a design fault. But Tweedledum needs to be aware of it.
