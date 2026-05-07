## Contract Note 006: Session and Auth Contract

**State:** agreed
**Contract Version:** v1.0-auth

**Finalized Shape:**

**POST /auth/register** — unauthenticated
- Request: {email, password}
- Response 200: {email, verified: false, slug: null, created_at}
- Response 400: {error: 'invalid_email' | 'password_weak' | 'email_exists', message: '...'}
- Behavior: Backend creates unverified user, sends verification email with token link, sets httpOnly session cookie.

**GET /auth/verify?token=X** — unauthenticated, link-based
- Response 200 + 302 redirect to /dashboard (or frontend handles via referrer)
- Behavior: Validates token (24h TTL), marks user verified, generates slug at this moment (uuid4 first 8 chars, collision-checked, lowercase). Sets httpOnly session cookie. Subsequent GET /auth/me will return slug.
- Response 400: Token invalid/expired, returns HTML error page (or JSON if API call), user must request new verification email.

**POST /auth/logout** — authenticated
- Request: (empty body or {})
- Response 204: No content
- Behavior: Invalidates session token (revokes cookie).

**GET /auth/me** — authenticated
- Response 200: {email, verified: true|false, slug: 'uuid8' | null, created_at}
- Response 401: User not authenticated, no body.
- Behavior: Returns current user state. Frontend calls on app init; if 401, redirects to login.

**Session Management:**
- httpOnly, Secure, SameSite=Strict cookies
- Session token: JWT or opaque token, 7-day TTL
- Verification tokens: single-use, 24h TTL, stored in `verification_tokens` table
- Password: argon2id hashing, salt per user
- Rate limiting: 5 attempts per IP per 15min on /auth/register and /auth/verify

**CSRF:**
- Deferred to Queen's domain for security assessment (contract-note-TBD)

**Backend Invariants:**
- A user with verified=true always has a slug allocated (unique, non-null, indexed).
- A user with verified=false always has slug=null.
- A slug is unique across all verified users (unique constraint on slug column where verified=true).
- A verification token is single-use (deleted after validation, cannot be reused).
- A session token cannot be used after logout (revocation list or token invalidation).

**Frontend Assumptions (Confirmed):**
- Frontend sends credentials in POST body, not Authorization header.
- Frontend relies on httpOnly cookie for session (never touches token in JS).
- Frontend reads user state via GET /auth/me (called on app init and after register).
- Frontend handles 401 by redirecting to login (session expired or invalid).

**Backward Compatibility:**
- v1.0 only; no prior versions.

**Failure Modes Handled:**
- Email service down: POST /auth/register succeeds (user created), email send fails (async retry queue or user can resend). Return 200 even if email fails (user can request resend).
- Token validation fails: return 400 with "token_invalid_or_expired"; user must request new email.
- Slug collision (rare): retry collision check + regenerate; log collision event for monitoring.
- Session token corrupted: return 401 from GET /auth/me; frontend redirects to login.

**Resolution:**
- ✅ Slug allocated at email verification time (GET /auth/verify), not registration.
- ✅ POST /auth/register returns user object with slug: null, verified: false.
- ✅ Session via httpOnly cookie (security boundary).
- 🔄 CSRF token — escalated to Queen's domain for ruling.

**Agreed by:** Tweedledum (2025-01-XX), Tweedledee (responding)
