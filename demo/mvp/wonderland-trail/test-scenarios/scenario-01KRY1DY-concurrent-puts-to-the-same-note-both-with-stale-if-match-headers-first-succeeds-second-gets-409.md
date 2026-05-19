## Scenario 349: Concurrent PUTs to the same note both with stale If-Match headers: first succeeds, second gets 409

**GUID:** 01KRY1DY1PSMHZM094C8W7E46P
**Severity:** breakage

**Setup:**

Note has revision_id='hash_T0'. Tab A and Tab B both load and cache 'hash_T0'. Tab C edits and saves the note, new revision_id='hash_T1'.

**Trigger:**

Tab A sends PUT with If-Match: hash_T0. Tab B sends PUT with If-Match: hash_T0 at nearly the same microsecond.

**Expected:**

First PUT (whichever server processes first) returns 409 with server_revision_id='hash_T1'. Second PUT also returns 409. Neither A nor B's edit is persisted.

**Concern:**

If both PUTs pass the If-Match check before either commits, they could both succeed and the second would overwrite the first.

**Property:**

For concurrent PUTs where the If-Match headers don't match the current state, all requests fail with 409 and no updates occur.

**Implies:**
- Implies SQLite transaction isolation must be SERIALIZABLE or use explicit locking.
