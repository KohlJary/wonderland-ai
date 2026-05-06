## Contract Note 005: Authentication & User Identity Contract

**State:** proposed → responded
**Contract Version:** (unlocked)

**Current Shape:**

None—the ADR assumes User table with email/password but the API contract is unspecified.

**Proposed Change:**

User registration, login, session token, and authenticated message send.

**POST /auth/register:**
- Request: `{ email, password, language_preference (enum: EN, DE, JA) }`
- Response: `{ user_id (UUID), email, session_token (opaque string), expires_in (seconds, default 24h) }`
- Password: hashed with bcrypt; plaintext never persisted
- Session token: either JWT (stateless, no server session table) or opaque ID (requires session table). Open: your preference?
- Email verification: out of scope v1; assume verified on registration
- Language preference: stored per user, used for message original_language and for partner matching (ADR: backend finds partner with matching language pair)

**POST /auth/login:**
- Request: `{ email, password }`
- Response: `{ user_id, session_token, expires_in }`
- Same token format as /register

**Session validation:**
All protected endpoints (send message, read chat, etc.) require `Authorization: Bearer <session_token>` header. Backend validates token and extracts user_id. If token is invalid or expired, return 401 Unauthorized. Token refresh: out of scope v1 (client re-authenticates when expired).

**User identity in messages:**
Message.sender_id references a user; frontend renders sender display name. Question: does the frontend need a /users/{id} endpoint to fetch user display name, or should the message object include sender display name as a denormalized field? Current proposal: include `sender_name` (string) in the message envelope so frontend does not need a separate user lookup. This is a denormalization; if users can edit their display name later, we need to decide: do old messages keep the old name, or do they update? (Deferred to fast-follow.)

**Source:** Ticket 001 (auth) specifies email/password but leaves API contract open. ADR specifies persistent user accounts but leaves session strategy open.

**Frontend Impact (Tweedledee):**

I'm comfortable with this contract. Here's my handling:

**Registration/Login flow:** Frontend renders two forms (register + login). On register, I collect email + password + language preference. On login, email + password. Both POST to /auth/{register|login}, receive `session_token` + `user_id` + `expires_in`. I store the token in **HttpOnly cookie** (if backend sets it) **or localStorage** (fallback if backend doesn't set HttpOnly). I also store `user_id` and `expires_in` locally to know when to warn user of expiry.

**Session token format:** I prefer **opaque token** (backend session table) over JWT. Why: I don't need to validate the token locally; I just pass it in the Authorization header and trust the backend to tell me 401 if it's bad. This keeps frontend simpler and avoids the version-skew problem where frontend's JWT validation logic diverges from backend's. Opaque also lets you rotate tokens server-side without requiring client update. If you insist on JWT, I'll decode and validate locally, but that's more complex.

**Token expiry handling:** If `expires_in` is set and non-null, I'll show a warning 5 minutes before expiry ("Session expires soon—refresh to continue"). On 401 response, I'll redirect to login. **No refresh token in v1**—user re-authenticates on expiry. This is acceptable for MVP.

**User identity in messages:** `sender_name` denormalized into the message envelope is perfect. I'll render it directly without a separate /users/{id} lookup. The immutable snapshot (set at send time, never updated if user edits name later) is the right choice for v1—it preserves message intent and sidesteps the "do old messages update?" problem.

**Client state:** I'll store `{ user_id, email, language_preference, session_token, token_expires_at }` in localStorage (or sessionStorage if we want logout on browser close). On app load, I'll check if token is expired; if so, show login form. All subsequent requests include `Authorization: Bearer <session_token>`. On 401, clear state and redirect to login.

**Open question for backend:** What's the expiry semantic? `expires_in` is seconds-from-now, right? And if token expires mid-session, I get 401 on the next request, not a proactive disconnect? Confirming so I handle error cases correctly.

**Backend Impact (Tweedledum):**

Backend owns user table, password hashing, session token generation and validation, and user_id extraction on protected endpoints. Denormalizing sender_name into messages requires care: either it's immutable (set at message creation time), or it's a foreign key and needs a join. Current proposal: immutable (set at send time, never updated). If user edits display name, old messages keep old name.

---

**Tweedledee's assessment:** I'm **marking this ready to agree**. The only open is token format (JWT vs opaque), and I've stated my preference (opaque). If you go JWT, I'll adapt; if opaque, that's ideal. No blocker either way.
