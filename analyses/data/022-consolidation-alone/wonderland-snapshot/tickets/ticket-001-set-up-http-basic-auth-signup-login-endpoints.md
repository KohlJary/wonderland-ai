## Ticket 001: Set up HTTP Basic auth (signup + login endpoints)

**Sources:** story/user-can-create-an-account-and-log-in-with-basic-auth
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1–2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: ticket/initiate-conversation-endpoint, ticket/send-message-endpoint
- Blocked by: —
- Soft: —

**Description:**

Implement POST /auth/signup (email, password, language_preference) and POST /auth/login (email, password) endpoints. Store users with password_hash. Return a session token or HTTP 200 on successful auth (confirm with Cat which session model is in scope). No logout endpoint for MVP. Minimal validation: email format, password length ≥8. Store users in a `users` table with id, email (unique), password_hash, display_name (default=email prefix), language_preference (default=EN), created_at, updated_at.

**Acceptance:**
- POST /auth/signup with valid email and password returns 200 and a user object (or session token, TBD with Cat)
- POST /auth/login with valid email and password returns 200 and a user object (or session token, TBD with Cat)
- Duplicate email on signup returns 409 or similar
- Weak password on signup returns 400
- Invalid email on login returns 401
- Invalid password on login returns 401
- Users table has all required columns; password is hashed (not plaintext)

**Risk:**

If the team chooses token-based auth over HTTP Basic, this ticket balloons to include token generation, storage, and expiry logic. Confirm the auth model with the Cat before starting.
