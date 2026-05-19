## Scenario: Concurrent PUT requests with stale If-Match headers get detected and rejected, not overwritten

**Severity:** breakage

**Setup:**
Note id=1 with title='original', body='hello', tags=['a']. Server computes initial revision_id = SHA256(sorted(['original', 'hello', [10], 'T0'])) = 'hash_T0'. 
Tab A loads the note, caches revision_id = 'hash_T0'. 
Tab B also loads the note, caches revision_id = 'hash_T0'.
Meanwhile, Tab C (different user or device) edits and saves the note. Body is now 'goodbye'. Server revision_id = 'hash_T1'.

**Trigger:**
Tab A sends PUT /notes/1 with If-Match: hash_T0, request body {title: 'edited_a', body: 'hello'}.
Tab B sends PUT /notes/1 with If-Match: hash_T0, request body {title: 'original', body: 'edited_b'} at nearly the same time.
Server processes both requests after Tab C's save has committed.

**Expected:**
The first PUT (whichever is processed first) returns 409 Conflict with {error: 'ConflictError', server_revision_id: 'hash_T1', server_state: {...}}.
The second PUT also returns 409 Conflict (or follows the first result depending on transaction ordering).
Neither Tab A nor Tab B's edits are persisted. The note remains in its Tab C state.
The user in Tab A sees a collision modal and can choose to reload or retry with the current revision_id from the 409 response.

**Concern:**
If the If-Match validation doesn't happen inside a serializable transaction (or with row-level locking), both requests might pass the validation before either one commits. Result: one edit overwrites the other silently, defeating collision detection.

**Property:**
For all concurrent PUT requests to the same note where the first request changes the revision_id, the second request detects the mismatch and fails with 409 before writing to the database.

**Implies:**
- Implies SQLite transaction isolation must be SERIALIZABLE or use explicit locking (IMMEDIATE or EXCLUSIVE transaction mode).
- Implies that the If-Match check must happen BEFORE any UPDATE statement commits, not after.
- Implies test must verify this with actual concurrent requests (not just sequential ones).

