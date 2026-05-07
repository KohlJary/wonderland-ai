## Scenario: Verification token is single-use (second attempt with same token fails)

**Severity:** silent-wrongness

**Setup:**

A user has just registered (email verified=false). A verification token has been generated and sent in email. The token is cryptographically signed and stored server-side with a 24h TTL.

**Trigger:**

User clicks the verification link and successfully verifies (first use). Token is consumed. User receives a verification-success response. The same email arrives again (e.g., user clicked back button, or automated email re-send). User clicks the verification link from the first email again (same token value).

**Expected:**

Second attempt with the same token should fail with 400 or 401. The user's verified status should remain true (from first verification). The system should not accept the second verification or create a secondary verified state.

**Concern:**

Verification tokens are often stored in a simple database table with {token, user_id, expires_at}. If the implementation does not explicitly mark the token as "consumed" after first use, a second GET /auth/verify with the same token will find the same row and verify the user again (idempotent, which is OK) — OR the token validation might not check for prior consumption at all, creating a window where a stolen/leaked token can be used multiple times.

The silent-wrongness is: if token reuse is allowed silently, an attacker who steals a verification token can re-verify a user's account multiple times, or (if the implementation is careless) use the token to verify a *different* account somehow.

**Property:**

For all verification tokens T and users U, if T is used to verify U successfully once, subsequent uses of T must either (1) return success idempotently (acceptable, same user), or (2) return 400/401 (single-use enforcement). A leaked token cannot verify a *different* user.

**Implies:**

Implies token-consumption data model decision — flag for Cat if the implementation defers token revocation to a later version or uses a questionable token-storage pattern.
