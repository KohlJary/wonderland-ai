## Ticket 007: Session management and auth persistence

**Sources:** sign-up-and-claim-my-homepage-url
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: markdown-publishing-setup, account-settings-view
- Blocked by: user-registration-and-email-verification
- Soft: —

**Description:**

User login / logout flow. Session state is validated on every authenticated request (e.g., when writing or editing homepage). CSRF tokens on forms. Logout clears session. Use secure, httpOnly cookies for session storage (no localStorage for auth tokens).

**Acceptance:**
- User can log in with email and password
- Session persists across page reloads
- Logout clears the session
- Unauthenticated users cannot POST to /homepage/:slug
- CSRF tokens are included in forms and validated

**Risk:**

CSRF and session fixation security; Queen will review before ship.
