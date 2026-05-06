## Ticket 001: User registration and auth (email + password v1)

**Sources:** directive, adr:translation-chat-data-model-persistence-translation-service-risk-and-user-identity
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1–2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: ticket:message-send-receive-pipeline, ticket:schema-and-persistence-layer
- Blocked by: —
- Soft: —

**Description:**

Implement email + password registration and login. Create user table; hash passwords; issue session tokens. Assume single-domain users (no federation) for v1. Return user ID and session token on successful login; enforce session on subsequent requests. Do not implement 2FA, social login, or password reset in v1.

**Acceptance:**
- User can register with email and password
- User can log in and receive a session token
- Session token is validated on protected endpoints
- Passwords are hashed (bcrypt or equivalent); plaintext never stored
- User ID is stable and queryable

**Risk:**

If user identity model needs to support federation or delegated auth (mentioned in ADR as open), this ticket will need rework. Clarify identity scope with Tweedledee before starting.
