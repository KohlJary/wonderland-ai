## Ticket 001: Implement authentication without friction for new users

**Sources:** story/new-user-understands-how-to-authenticate-without-friction
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1.5–2.5 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: ticket/monolingual-exchange-backend
- Blocked by: —
- Soft: —

**Description:**

Implement signup and login flow per the new-user story acceptance criteria. Scope: OAuth integration (email or federated) with email verification, session management, no CAPTCHA gate. Out of scope: multi-factor auth, recovery flows. The flow should feel immediate to the user — no more than 2 redirects, no more than 90 seconds of perceived latency.

**Acceptance:**
- User can sign up with email in under 2 minutes
- User can log in with stored credentials
- Session persists across tab reload
- Invalid credentials fail gracefully with clear messaging

**Risk:**

Federated OAuth setup can take longer than expected if provider docs are unclear. Expand to 3 days if we hit provider friction.
