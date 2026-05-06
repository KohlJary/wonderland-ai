## Ticket 007: Basic authentication (signup/login/logout) — FAST-FOLLOW

**Sources:** story: new-user-joins-and-authenticates-for-the-first-time
**Owner:** tweedledum
**Tier:** fast-follow
**Estimate:** 1.5-2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: user-model-with-language-capability-schema
- Soft: queen-ruling-on-session-storage-security

**Description:**

Implement signup (username + password), login (session token), logout. Skeleton code may have partial auth; if so, complete it. No social login, no password reset, no email verification in v1. Session token stored in secure HTTP-only cookie or localStorage (security decision deferred to Queen if not already ruled).

**Acceptance:**
- POST /auth/signup creates User and returns session token
- POST /auth/login verifies password and returns session token
- POST /auth/logout invalidates session
- Protected endpoints (message send/receive) require valid session
- No plaintext passwords in logs or error messages

**Risk:**

Password storage method must pass Queen's review. If Queen requires bcrypt with minimum iteration count, confirm choice early. Also: session storage (cookie vs. localStorage) is a security decision that may extend estimate if not pre-decided.
