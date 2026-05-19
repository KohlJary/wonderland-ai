## Scenario 270: Concurrent save requests to the same note are serialized: the second request waits for the first to complete before comparing revision_ids

**GUID:** 01KRY19VMP015JW631HNJ74GC4
**Severity:** degradation

**Setup:**

Note #1 has revision_id_old=hash(initial_state). Two concurrent HTTP requests arrive within microseconds of each other, both attempting PUT /notes/1 with If-Match: revision_id_old and different new states (A and B).

**Trigger:**

Request 1 and Request 2 both attempt to acquire a row lock on note #1 and compare their revision_id against the server's current revision_id. Request 1's comparison happens first.

**Expected:**

Request 1's save succeeds (revision_id matches), the note is updated, revision_id_new_A is computed, and the row lock is released. Request 2 then acquires the lock, compares its client revision_id_old against the server's new revision_id_A (mismatch), returns 409 with the server state and revision_id_A. Both requests are serialized — the database ensures no race condition where both reads see the old revision_id before either write completes.

**Concern:**

If the backend does not use database-level row locks (or equivalent transaction isolation), two concurrent requests might both read the same old revision_id, both pass the check, and both write, resulting in a lost update. This is the classic optimistic locking failure. Or the backend might use application-level locking (like a mutex) which works in a single-process app but fails if the backend is deployed as multiple instances behind a load balancer — each instance has its own mutex, so requests to different instances can still race.

**Property:**

For all pairs of concurrent save attempts to the same note with different client revision_ids, the database's transaction isolation level ensures that one read-compare-write completes before the other read-compare-write begins. This is the serializable (or repeatable-read) isolation level in SQLite (SQLite's default DEFERRED transaction mode provides this for writes).

**Implies:**
- Requires database transaction isolation level check — flag for Tweedledum to verify SQLite's isolation behavior.
- Requires test coverage of concurrent requests (using threading or async simulation) to verify no lost updates.
