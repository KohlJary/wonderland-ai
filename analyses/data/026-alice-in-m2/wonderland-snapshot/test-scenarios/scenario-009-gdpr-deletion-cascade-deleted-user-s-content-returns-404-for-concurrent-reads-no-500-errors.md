## Scenario 009: GDPR deletion cascade: deleted user's content returns 404 for concurrent reads, no 500 errors

**Severity:** breakage

**Setup:**

User A publishes to /~alice. User B reads /homepage/alice. User A initiates DELETE /auth/me (cascades user → homepage → content).

**Trigger:**

At T=0: DELETE /auth/me begins. At T=5ms: GET /homepage/alice arrives. At T=10ms: delete commits.

**Expected:**

User B's read either succeeds (read-before-delete) or returns 404 (read-after-delete). No 500 errors. No partial data. Cascade is atomic.

**Concern:**

Delete cascade might not be atomic. Reads hit stale data, foreign key violations, or race conditions result in inconsistent state.

**Property:**

For all users U and requests R: if U deletes at T and R in flight at T, result is 200 or 404, never 500. Reads never blocked indefinitely.
