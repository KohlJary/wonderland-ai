## Scenario: Account deletion — cascade, atomicity, and concurrent session invalidation

**Severity:** breakage + silent-wrongness

**Setup:**

Sam has an active account with a homepage and is logged in on two devices. Device A has a valid session token; Device B has a valid session token. Sam initiates account deletion from Device A and confirms the password. The system receives the DELETE /user/me request, with token_A in the Authorization header.

**Trigger:**

Backend validates token_A is authentic and not yet revoked. Backend validates password is correct. Backend begins cascading deletion:

1. Delete homepage record (any content is gone)
2. Delete user record
3. Invalidate all sessions for this user (including token_A and token_B)

Meanwhile, Device B has queued a request to fetch the homepage (GET /user/sam) and is about to send it using token_B.

**Expected:**

1. **Atomicity** — Either all three deletions succeed together, or the entire transaction rolls back. Partial deletion (user deleted, homepage orphaned) is corrupt state.
2. **Cascade correctness** — When the user is deleted, no orphaned homepages, no orphaned sessions, no references to a non-existent user in logs.
3. **Session invalidation** — All tokens for this user become invalid immediately. Token_A's DELETE request succeeds (user is still valid when we check it). Subsequent requests with token_B fail with 401 "token revoked" or 403 "user no longer exists."
4. **Idempotency** — If Device A sends the DELETE request twice (due to retry logic or network duplication), the second request is safe: returns 404 "user already deleted" or 400 "invalid token" (because the user no longer exists and the token is revoked). No error cascade.
5. **Verification** — The deleted username becomes available for someone else to claim. (This is separately tested: username uniqueness survives deletion.)

**Concern:**

Account deletion is where GDPR compliance lives. Common failure modes:

1. **Incomplete cascade** — User deleted, homepage orphaned. Orphaned homepages appear in discovery (/discover lists a user who no longer exists). Or: audit logs still reference the user but user is gone, causing FK violations on later queries.
2. **Non-atomic deletion** — User deleted successfully, but session invalidation fails partway through. Some old tokens are revoked, some aren't. A token that thinks the user still exists gets rejected by the auth check but then succeeds because we fall back to checking the user table—which is now empty.
3. **Session revocation timing** — Token_B's request arrives during the transaction. Does it see "user exists" and succeed in fetching a homepage that's about to be deleted? Or does it fail with 404? Timing matters.
4. **Idempotency failure** — Second DELETE /user/me request from Device A. If there's no idempotency check, this might fail loudly (500 error) instead of safely (404). User gets confused; thinks something went wrong; tries again.

The system must handle all of these. This is one of the most dangerous scenarios in the app.

**Property:**

For all users U with account A and active sessions S1, S2:
- When U deletes account A:
  1. All homepages and content associated with U are inaccessible (404 or gone).
  2. All sessions in S1, S2 become invalid (401 on next authenticated request).
  3. U's username becomes available for re-registration.
  4. All related data (audit logs, if any) are purged or orphaned cleanly (no FK violations).
  5. Subsequent requests with old tokens fail safely (401 or 404), not with 500 errors.

Additionally: DELETE /user/me is idempotent. If called twice with a valid token, the first succeeds (204), the second returns 404 or 410. Neither causes a 500 or corrupt state.

**Implies:**

Implies database transaction design (Tweedledum's domain—backend). Implies session table schema and revocation logic. Implies audit logging (if the Queen requires it). Implies contract clarification: does homepage cascade immediately, or is there a grace period? Assume immediate for v1.

Implies testing strategy: the concurrent-session-during-deletion scenario is hard to test deterministically. May require explicit transaction pause points in tests or careful timing.

---

## Notes for Test Implementation

The pytest tests will:

1. Register a user, log in on two devices (get two tokens).
2. POST to update homepage (so there's content to cascade).
3. From device A, DELETE /user/me with password.
4. Assert deletion succeeds (204).
5. Assert subsequent GET /user/{username} returns 404 or empty.
6. Assert token_B is now invalid (GET with token_B returns 401).
7. Assert the username can now be claimed by someone else (new registration succeeds).
8. Test idempotency: second DELETE /user/me returns 404 or 410, not 500.

This test will FAIL until cascading deletion and session invalidation are implemented correctly.
