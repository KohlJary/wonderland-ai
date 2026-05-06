## Contract Note 002: User identity and language-pair matching

**State:** proposed (awaiting resolution)
**Contract Version:** (unlocked)

**Current Shape:**

ADR assumes User table with email/password, user self-selects language preference on signup, backend finds one other user with matching pair. No /users endpoint exposed (mitigate enumeration risk). Identity model is open: persistent user account (email verified) or guest session?

**Proposed Change:**

Frontend needs explicit contract on auth and user context: (A) JWT session tokens issued on login, token included in all subsequent requests; (B) user context endpoint returns { user_id, email, language_preference, active_conversation_id } after auth; (C) conversation entity is opaque to user (user doesn't select partner or see partner's user_id until matched; backend assigns partner). User ID must be stable and included in messages for attribution.

**Source:** ticket:user-registration-and-auth + ADR tradeoff on user enumeration risk and identity model. Ticket 001 assumes email/password, not guest; needs clarification on session token format and whether frontend needs to refresh tokens.

**Frontend Impact (Tweedledee):**

I'm building login form (email + password), storing session token locally (localStorage or sessionStorage + HttpOnly cookie if possible). Frontend renders login → user context fetch → conversation fetch → chat UI. If user context endpoint doesn't return active_conversation_id, I have to query a separate /conversations endpoint; if it does, single fetch. Also: frontend needs to know if session tokens expire; if so, I need to handle refresh token exchange or force re-login.

**Backend Impact (Tweedledum):**

Persistent User account with email/password (per ticket 001). Opaque session tokens (stateful, not JWT). Here's the contract:

**User table schema:**
- user_id (UUID primary key)
- email (string, unique, indexed)
- password_hash (string, bcrypt)
- language_preference (enum: 'EN', 'DE', 'JA')
- created_at, updated_at

**POST /auth/register:**
- Request: `{ email, password, language_preference }`
- Response (201): `{ user_id, email, session_token (opaque string, 32-char hex or equivalent), expires_in (seconds, default 86400 = 24h), token_type ('Bearer') }`
- Backend: hash password with bcrypt (cost 10), INSERT user, generate session_token and store in session table, return token with 24h TTL
- Email verification: out of scope v1; assume email is valid on registration
- Duplicate email: return 409 Conflict

**POST /auth/login:**
- Request: `{ email, password }`
- Response (200): same as /register response
- Backend: query user by email, bcrypt.verify(password, password_hash), generate new session token if match, return; else 401 Unauthorized

**Session validation:**
- All protected endpoints require `Authorization: Bearer <session_token>` header
- Backend validates token against session table (select session where token = ? and expires_at > now())
- If valid: extract user_id from session record, proceed; else return 401 Unauthorized
- Session tokens are stateful (stored in DB); no JWT (avoids clock skew and replay attack surface)
- Token refresh: out of scope v1. When token expires, client re-authenticates (POST /auth/login again). No refresh token mechanism.

**Language-pair matching:**
- Conversation entity: `{ conversation_id (UUID), user_1_id (FK to User), user_2_id (FK to User), language_pair (enum: 'EN-DE', 'EN-JA'), created_at }`
- When user logs in (POST /auth/login), backend checks if user already has an active conversation. If yes, return active_conversation_id in the login response. If no, backend queries for another user with matching language_preference, creates a conversation record, and returns conversation_id in login response.
- Partner anonymity: frontend never sees user_2_id or user_2_email. Messages include sender_id (for attribution), but frontend does not have a /users endpoint to resolve sender_id to a name. Instead, messages include sender_display_name (denormalized, set at message creation time to user.email or a derived display name).

**GET /auth/user (user context endpoint):**
- Request: header `Authorization: Bearer <session_token>`
- Response (200): `{ user_id, email, language_preference, active_conversation_id (UUID or null if no active conversation) }`
- Backend: validate token, query user and (optionally) active conversation, return JSON

**User deletion (GDPR 17):**
- Frontend initiates DELETE /auth/user
- Backend: soft-delete user record (UPDATE users SET deleted_at = now()), cascade delete to conversations (set deleted_at), cascade delete to messages (set deleted_at)
- Do not hard-delete; keep records for audit trail and potential legal hold
- All subsequent login attempts with that email fail (401, or optionally 410 Gone)

**Invariants enforced:**
- Email is unique (UNIQUE constraint on users.email)
- User_id is stable (UUID, never changes, even after deletion)
- Password is never stored plaintext (always bcrypt hash)
- Every conversation has exactly two users (CHECK constraint on conversation creation)
- Session token is unique and opaque (no JWT that frontend can parse)
- A user cannot have two active conversations with overlapping language pairs (application-level constraint: when creating a conversation, query for user's existing conversations; if any match the language pair, reject or return the existing one)

**Known limitations:**
- No token refresh: when a token expires, the user must re-login. This is a UX cost but simplifies the implementation for v1.
- Session table grows unbounded (old, expired sessions are never deleted). Mitigate with a background job to delete sessions older than 30 days. Defer to fast-follow.
- User enumeration via language matching is still possible via timing attacks (e.g., "login with language X takes N ms when there's a match available" vs "takes M ms when no match"). Acceptable for v1 (threat model is two consenting users sharing a translation chat, not a sophisticated attacker); escalate to Queen if threat model changes.
- No 2FA, password reset, or email verification. These are out of scope v1.

**Questions for Tweedledee:**
- Token storage: you mentioned HttpOnly cookie as an option. If you use HttpOnly cookie, you don't need the Authorization header; the cookie is auto-sent. Does this work for your frontend stack?
- Display name: I'm proposing to denormalize sender_display_name into each message (set once at send time). This means if a user edits their display name later, old messages keep the old name. Is this acceptable?
- Active conversation on login: I'm returning active_conversation_id in the login response so you can skip a separate /conversations endpoint fetch. Is this helpful?

**Resolution:** proposed — awaiting frontend feedback on token storage and display name semantics.
