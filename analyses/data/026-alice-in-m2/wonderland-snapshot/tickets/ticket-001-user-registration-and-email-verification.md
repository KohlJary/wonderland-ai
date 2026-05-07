## Ticket 001: User registration and email verification

**Sources:** sign-up-and-claim-my-homepage-url
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 1–2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: homepage-url-reservation, markdown-publishing-setup
- Blocked by: —
- Soft: —

**Description:**

Implement user registration flow with email verification. User signs up with email + password, receives verification link, confirms ownership of email address. After verification, user account is active and ready for homepage creation. Auth state is persisted and validated on subsequent logins.

**Acceptance:**
- User can register with email and password
- Verification email is sent to the provided address
- User can verify email via link and become active
- Login succeeds for verified users, fails for unverified or non-existent users
- Session persists across page reloads

**Risk:**

Email delivery reliability; consider a sandbox/test mode for development. SMTP configuration may require security review.
