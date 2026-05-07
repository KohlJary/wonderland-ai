## Ticket 002: User authentication and session management

**Sources:** sign-up-and-claim-a-username
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1-1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: edit-my-homepage-in-markdown
- Blocked by: user-registration-and-username-claim
- Soft: —

**Description:**

Implement login/logout, session tokens, and authentication middleware. User logs in with email + password. System issues a session token (JWT or opaque, team decision). Middleware protects authenticated routes. Logout clears session. Handle token expiry gracefully.

**Acceptance:**
- User can log in with registered email and password
- Session token is issued and stored client-side
- Authenticated endpoints require valid token
- Logout clears session and invalidates token
- Expired tokens are rejected and user is redirected to login
- Session persists across page refreshes until logout or expiry

**Risk:**

Token expiry and refresh token flow can create subtle bugs; may need a second pass after Dormouse observes production behavior.
