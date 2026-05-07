## Scenario: User deletes account (GDPR) while other users are reading their homepage

**Severity:** breakage

**Setup:**

User A has published content to /~alice. User B is reading User A's homepage. User A initiates account deletion (DELETE /auth/me or equivalent). The backend begins purging all User A's data per GDPR requirements.

Concurrently, User B's GET /homepage/alice request is in flight.

**Trigger:**

At T=0: User A sends DELETE /auth/me. Backend begins transaction: delete user record, delete homepage record, delete content record.
At T=5ms: User B's GET /homepage/alice request arrives.
At T=10ms: Delete transaction commits (user, homepage, content all deleted).
At T=15ms: User B's read transaction executes and discovers the homepage is gone.

**Expected:**

User B's GET /homepage/alice should either:
1. Return the content (read-before-delete: B's read started before A's delete committed)
2. Return 404 (read-after-delete: the homepage no longer exists)

What should NOT happen:
- Return 500 Internal Server Error (query crash)
- Return partial/corrupted data (half-deleted content)
- Block indefinitely (B's read waits forever for A's delete to finish)

**Concern:**

The cascade is: user deletion → homepage deletion → content deletion. If these are not atomic, the following could occur:

1. User record is deleted, but homepage still exists with orphaned user_id reference.
2. GET /~alice queries the user table (returns NULL), then tries to return the user's homepage (foreign key constraint violated or stale data).
3. Concurrent reads might encounter stale data, corrupted records, or referential integrity violations.

The breakage is: User B gets a 500 error, or receives partial/nonsensical data, or experiences a long timeout.

**Property:**

For all users U and requests R, if U initiates deletion at T and R (a read of U's data) is in flight at T, the final result is either (1) R returns data (R committed before delete), or (2) R returns 404 (R committed after delete). No 500 errors. No partial data. Reads are never blocked indefinitely.

**Implies:**

Implies transaction isolation level and cascade behavior — flag for Cat if the deletion uses a naive "delete user, delete homepage, delete content" sequence without proper transaction boundaries or cascade constraints.

Implies account deletion endpoint specification — this scenario cannot be tested until DELETE /auth/me or equivalent is implemented.
