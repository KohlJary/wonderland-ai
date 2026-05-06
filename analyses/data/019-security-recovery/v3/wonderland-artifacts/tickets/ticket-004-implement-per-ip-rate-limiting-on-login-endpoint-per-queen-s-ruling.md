## Ticket 004: Implement per-IP rate-limiting on /login endpoint per Queen's ruling

**Sources:** ruling: rate-limiting-on-login-endpoint-immediate-hardening-required, ticket: implement-rate-limiting-and-account-lockout-hardening-to-stop-credential-stuffing-attack
**Owner:** Tweedledee & Tweedledum
**Tier:** v1
**Estimate:** 4-6 hours, 80% confident
**Status:** open

**Dependencies:**
- Blocks: ticket: implement-account-lockout-policy-and-user-notification
- Blocked by: —
- Soft: ticket: cat-architecture-confirmation-rate-limit-composition-with-middleware

**Description:**

Implement per-IP rate-limiting on POST /auth/login endpoint. Queen ruling requires: (1) rate-limit threshold enforcement after N failed attempts from single IP; (2) backoff policy (duration, shape); (3) integration with existing FailedAttempt tracking in models.py. Do not implement email-based rate-limiting (distributed-IP bypass); that is fast-follow. Compose with existing session middleware. Add src/auth/rate_limit.py if architecture supports it; modify src/auth/endpoints.py to call rate-limit check before login attempt.

**Acceptance:**
- Rate-limit triggering confirmed in tests after N failed attempts from single IP
- Backoff duration enforced; subsequent requests from same IP rejected before auth attempt
- FailedAttempt table records are created for each attempt (for observability and breach-notification)
- Legitimate traffic from shared IPs (office networks) can still attempt login from different user accounts

**Risk:**

Backoff duration choice is empirical (too short = ineffective; too long = DoS users on shared IPs). Start conservatively (5min backoff after 20 attempts); Dormouse will surface if real users are affected.
