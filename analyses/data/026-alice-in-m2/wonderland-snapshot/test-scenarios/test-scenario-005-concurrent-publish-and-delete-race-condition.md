## Test Scenario 005: Concurrent Publish and Delete — Race Condition Corrupts State

**Severity:** breakage

**Setup:**

User alice has published homepage content (/homepage/alice). Two requests arrive at nearly the same time, both targeting alice's account:
1. POST /homepage/alice/publish (frontend republishing content)
2. DELETE /auth/delete-account (alice closing her account in another browser tab or from another device)

Both requests are processed concurrently (no explicit locking or transaction isolation).

**Trigger:**

Request 1 begins: acquires write lock on content row (or doesn't acquire any lock).
Request 2 begins: acquires delete lock on user and homepage rows.
Request 1 completes: updates content row, returns 200.
Request 2 completes: deletes user, cascades to homepage (but content row is orphaned or becomes inconsistent).

**Expected:**

Final state is clean and consistent:
- Scenario A: Request 1 wins. Content is published and current. User is NOT deleted (alice can verify this by logging in).
- Scenario B: Request 2 wins. User is deleted. Content is deleted (cascade delete or soft-deleted and inaccessible).
- No Scenario C: User is deleted but content row remains (orphaned reference). GET /homepage/alice returns dangling error.

No half-state, no inconsistency, no corruption.

**Concern:**

Concurrent database operations without proper isolation can corrupt state. If the publish transaction and delete transaction are not isolated, the database can end up in an inconsistent state:
- Content row points to a deleted homepage.
- Homepage points to a deleted user.
- Queries to retrieve content fail unexpectedly or return dangling references.

This is a classic database concurrency bug. Without transaction isolation or row-level locking, the system becomes unreliable. This is breakage because data corruption is unacceptable.

**Property:**

Concurrent operations on the same user's data (publish and delete) must result in a clean, consistent final state (not a mixed state).

Formally: If delete(user) and publish(user) execute concurrently, the final state of (users, homepages, content) tables must satisfy the invariant that either:
1. User exists, homepage exists, content exists (publish won, delete lost).
2. User deleted, homepage deleted, content deleted or inaccessible (delete won, publish was overridden).

No state where user is deleted but content is still queryable.

**Implies:**

- Requires database transaction isolation: Serializable or Repeatable Read isolation level.
- Requires row-level locking: UPDATE/DELETE operations acquire locks that block concurrent writes.
- Requires cascade delete with foreign key constraints: DELETE user CASCADE to homepages and content.
- Implies test is difficult to write (concurrency simulation requires threading or careful timing). For v1, documenting the boundary and verifying isolation level is sufficient.
- Implies post-delete test: after account deletion, verify content is inaccessible (no orphaned queries).
