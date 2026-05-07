## Contract Note 009: User registration and email verification flow

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

none yet

**Proposed Change:**

POST /auth/register with {email, username, password}. Backend validates email format, checks username uniqueness (case-insensitive, returns conflict + alternatives if taken), hashes password (bcrypt, 12 rounds), creates user record with status=unverified, sends verification email with token. Token is single-use, expires 24h. Frontend submits token via GET /auth/verify?token=<token> (or POST /auth/verify if preferred). On verify success: user status=active, user can log in.

**Source:** ticket-001 (registration); ticket-002 (auth)

**Frontend Impact (Tweedledee):**

Frontend renders registration form with email + username inputs. Validation on blur: check email format, check username length (suggest 3-20 chars), warn on reserved names if you have any. On submit, POST /auth/register {email, username, password}. Handle error states: (1) username conflict → show suggested_usernames in dropdown, (2) email already registered → show 'account exists, go to login' message, (3) invalid format → show field-level errors. After successful registration, show 'check your email' message. On verification email click, user lands on /verify?token=<token>—frontend could display 'verifying...' with JS calling POST /auth/verify {token} to complete (rather than clicking a raw link), which gives us control over redirect. On verify success: show 'verified, please log in' and redirect to /login. On verify failure: show error + 'request new link' button (maps to POST /auth/register-resend-verification or similar—do we need that endpoint?).

**Backend Impact (Tweedledum):**

Users table: id (PK), email (UNIQUE), username (UNIQUE COLLATE NOCASE), password_hash (bcrypt, cost 12), status (ENUM: unverified, active, deleted), created_at, updated_at. Verification_tokens table: id (PK), user_id (FK), token (UNIQUE), expires_at, used_at (nullable). Invariants: (1) user status stays unverified until verify endpoint is called; (2) token is single-use (checked via used_at on second verify); (3) username globally unique, case-insensitive lookup. Failure modes: lost token → user requests new (rate-limit 3/hr); concurrent register + verify → second verify idempotent (checks used_at first, succeeds silently if user already active). Open question: auto-login after verify or redirect to login form? (Affects session handling in contract 010.)
