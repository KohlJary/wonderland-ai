## Contract Note 010: Session token and authentication

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

none yet

**Proposed Change:**

POST /auth/login with {email, password}. Backend authenticates (bcrypt verify), issues session token (JWT, RS256, includes user_id + username, expires 7 days). Token stored in httpOnly cookie (name: session_token, secure flag, sameSite=lax) OR client-side localStorage (your call; cookie is more secure, localStorage is easier for SPA). On authenticated request: Authorization header Bearer <token> or cookie auto-sent. Middleware validates signature + expiry. POST /auth/logout clears cookie/token. GET /auth/me returns {user_id, email, username} if authenticated.

**Source:** ticket-002

**Frontend Impact (Tweedledee):**

On /login success, I expect {token, user: {user_id, username, email}}. I will store token in httpOnly cookie (you set Set-Cookie header on login response) if you confirm the cookie handling: (a) I never read it directly, (b) browser auto-attaches it to requests, (c) on logout you clear it, (d) on 401 I redirect to login. Alternatively, if you prefer header-based auth, I'll store JWT in localStorage and include Authorization: Bearer <token> on every request. I prefer cookie for security (no XSS exfil) but your choice—just confirm which. Refresh token question: I agree single 7-day token is simpler for v1; no refresh needed. On 401 response, I clear stored token and redirect to /login. On logout success, I clear token. GET /auth/me I'll call on app startup to hydrate auth state (show 'logged in as {username}' in header). Question: should /auth/me return minimal {user_id, username, email, is_admin?} or more? I'm assuming minimal.

**Backend Impact (Tweedledum):**

JWT RS256, payload: user_id, username, issued_at, expires_at (7 days). Private key server-side, public key for middleware verification. Issued on successful POST /auth/login (email + password, bcrypt verify against users.password_hash). Token delivery: httpOnly cookie (Secure, SameSite=Lax) preferred for security. Middleware validates JWT signature + expiry on protected endpoints; 401 if invalid/expired. POST /auth/logout clears cookie. GET /auth/me returns {user_id, email, username} if authenticated. Invariants: (1) token not issued for unverified user (check status=active in login); (2) expired token invalid (middleware enforces). Failure modes: token leaked → no server-side revocation (JWT stateless); rely on 7-day expiry; token expired → 401, frontend clears session. No refresh tokens in v1 (single 7-day token simpler).
