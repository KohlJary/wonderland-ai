## Contract Note 001: Auth session and cookie contract

**State:** agreed
**Contract Version:** v1 (auth-sessions-httponly-cookies)

**Current Shape:**

Session-based auth using httpOnly, Secure cookies. POST /auth/register and POST /auth/login return Set-Cookie headers. GET requests include session cookie automatically. Unauthenticated POST to /homepage/:slug returns 401 Unauthorized with JSON error body. CSRF tokens in POST bodies or headers (specified below).

**Proposed Change:**

POST /auth/register — user submits {email, password}. Backend creates unverified user, sends verification email. Response: 200 with {user_id, email, verified: false} in body + Set-Cookie (session token). GET /auth/verify?token=X — validates token, marks user verified. Response: 200 with {user_id, email, verified: true} + Set-Cookie (refreshed session). POST /auth/login — user submits {email, password}. Response: 200 with {user_id, email, verified: true} + Set-Cookie. POST /auth/logout — invalidates session. Response: 204 No Content + Set-Cookie (expires). GET /auth/me — returns {user_id, email, verified: true} or 401 if not authenticated. All POST endpoints that modify state require CSRF token in X-CSRF-Token header.

**Source:** ticket-001 (user registration), ticket-007 (session management)

**Frontend Impact (Tweedledee):**

Frontend will: (1) POST /auth/register with {email, password}, handle 200 response and redirect to verification flow; (2) POST /auth/login with {email, password}, handle 200 response and redirect to editor; (3) attach CSRF token to publish POST in X-CSRF-Token header; (4) handle 401 responses by redirecting to login. Session cookie is automatic; frontend does not manage tokens in localStorage.

**Backend Impact (Tweedledum):**

Database: users table with (id, email, password_hash, verified_at, created_at, updated_at). Verification tokens table (single-use, 24h TTL, indexed by token + user_id). Session tokens (httpOnly cookies, 7d TTL, revocable via session table with user_id + token_hash + expires_at). Password hashing via argon2. Email service integration (SMTP or async queue). Rate limiting on /auth/register and /auth/verify to prevent enumeration/brute-force. CSRF token generation: random 32-byte token per session, stored in server memory (session store) with session, validated on POST. 401 response body: {error: 'unauthorized', message: 'Session expired or invalid'} (JSON). Session refresh: Set-Cookie on /auth/verify and /auth/login to ensure fresh 7d TTL. Password reset flow (POST /auth/forgot-password, GET /auth/reset?token=X) deferred to v2 (not in v1 scope).

**Resolution:** agreed — seam is well-defined. Frontend and backend align on httpOnly cookies + CSRF header + 401 response shape. CSRF token is server-generated per-session; frontend reads it from either (a) initial HTML page load (injected in meta tag or hidden form field — coordination needed if frontend framework expects it inline) or (b) GET /auth/csrf endpoint that returns token. Defer CSRF token delivery mechanism to next thread (frontend framework will determine whether meta-tag injection or separate endpoint is cleaner). For now: backend will generate and validate CSRF tokens; frontend will attach to X-CSRF-Token header on all POST requests that modify state.

**Resolution:**

Agreed. Frontend and backend align on httpOnly cookies + CSRF token header. Both 001 and 006 propose the same contract; consolidating. CSRF token delivery mechanism (meta-tag injection vs. separate GET endpoint) deferred to implementation thread (frontend framework will determine).
