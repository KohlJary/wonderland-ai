## Implementation 001: HTTP Basic Auth: signup and login endpoints

**Side:** backend
**Ticket:** ticket-001
**Contract:** contract-002 v1 (HTTP Basic stateless; no tokens; POST /auth/login returns {user_id, email, display_name, language_preference})
**Ready for review:** yes

**Approach:**

POST /auth/signup accepts {email, password, display_name, language_preference}, hashes password with bcrypt, stores user in DB, returns user object (no token). POST /auth/login accepts email+password in request body, validates against password_hash, returns user object. Middleware validates Authorization: Basic header on protected routes by splitting header, base64-decoding to email:password, looking up user by email, validating password. Rejects malformed or missing Basic headers with 401. All password validation happens server-side; frontend never holds plaintext in transit.

**Invariants Enforced:**
- exactly one user per email: unique constraint on users.email
- password never stored plaintext: password_hash only, bcrypt cost 12
- every user has a display_name: not-null constraint on users.display_name
- every user has a language_preference: not-null constraint on users.language_preference, default 'en'
- authorization header is validated on every protected request: middleware enforces before route handler

**Schema Changes:**

Initial schema: users table (id, email unique, password_hash, display_name, language_preference, created_at). No migrations from prior state (this is the first schema). Table is reversible by DROP TABLE if needed; no dependent tables yet.

**Failure Modes Handled:**
- Malformed Basic header (missing or non-base64): 400 Bad Request
- Missing Authorization header on protected route: 401 Unauthorized
- Email not found in DB: 401 Unauthorized (does not leak whether email exists)
- Password mismatch: 401 Unauthorized (does not leak password state)
- Database write fails during signup: 500 Internal Server Error; transaction rolls back, user not created
- Bcrypt hashing timeout (slow password): handled by bcrypt timeout config; user gets 500 if hash exceeds deadline

**Files:**
- src/models.py: Users model with email (unique), password_hash, display_name, language_preference, created_at
- src/auth.py: bcrypt hashing + validation; Authorization: Basic header parsing and validation middleware
- src/routes/auth.py: POST /auth/signup and POST /auth/login endpoints
- migrations/0001_initial.sql: users table schema with email unique constraint

**Known Limitations:**
- No password reset flow in v1 (deferred to later story if required)
- No rate limiting on auth endpoints (QA/Dormouse should monitor signup/login attempt patterns)
- No email verification in v1 (accepts any string as email; later story may require verification)
