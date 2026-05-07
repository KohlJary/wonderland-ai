## Scenario: User attempts to tamper with session cookie (modify, forge, replay)

**Severity:** breakage

**Setup:**

A session cookie has been issued to User A in the form of an httpOnly cookie with a session token. The token is validated server-side against the session store (in-memory or database). User B has captured User A's session cookie (via man-in-the-middle, XSS on another site, or packet sniffing over unencrypted connection).

**Trigger:**

User B sends an HTTP request with the captured (but now stale or modified) session cookie. The backend receives the request and validates the token.

Scenario variants:
1. **Token reuse**: User B uses the same token after User A has logged out (token was revoked).
2. **Token forgery**: User B creates a fake token that looks valid but was never issued by the server.
3. **Token modification**: User B modifies a valid token (e.g., changes the user_id field if the token is not cryptographically signed).
4. **Token replay**: User B uses a valid token, but the server's clock is out of sync, causing the token to appear valid when it should be expired.

**Expected:**

All variants should result in 401 Unauthorized. User B should not be able to:
- Access User A's account or data
- Perform actions on behalf of User A
- Create a new account using User A's email

**Concern:**

If the session token is not cryptographically signed (e.g., it's just a random user_id), User B could forge a token by guessing or modifying the user_id. If the token is not validated against a server-side session store, revoked tokens (from logout) might still be accepted. If the token format is predictable (sequential IDs), User B could forge tokens for other users.

The breakage is: User B gains unauthorized access to User A's account.

**Property:**

For all session tokens T and users U, if T is issued to U, then:
1. Only U can use T to authenticate.
2. Only the server that issued T can validate T (T cannot be forged by clients).
3. If T is revoked (logout, account deletion), subsequent use of T returns 401.
4. If T is tampered with (modified by client), validation fails (401).

**Implies:**

Implies a session token scheme (e.g., cryptographically signed JWT, opaque token with server-side store, etc.) — flag for Cat if the implementation uses a predictable or forgeable token format.
