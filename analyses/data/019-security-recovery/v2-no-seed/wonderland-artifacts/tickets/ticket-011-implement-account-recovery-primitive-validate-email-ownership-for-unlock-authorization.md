## Ticket 011: Implement account-recovery primitive: validate email ownership for unlock authorization

**Sources:** adr slug=decouple-unlock-authorization-from-initial-authentication, story slug=affected-user-can-regain-access-without-waiting-forever-or-jumping-through-chaos
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 2-3 hours, 70% confident
**Status:** open

**Dependencies:**
- Blocks: implement-account-unlock-workflow-for-rate-limited-users-email-link-or-sms, add-unlock-account-cta-to-login-page-for-locked-out-users-who-know-their-credentials
- Blocked by: queen-ruling-on-account-recovery-primitive-acceptable-for-unlock-authorization
- Soft: implement-rate-limiting-on-login-endpoint-per-queen-ruling

**Description:**

Implement the recovery primitive the Queen authorizes for account unlock. Minimal scope for incident response: email-based token validation (user requests unlock, we email a time-limited token, they return the token to complete unlock). The token must be independent of the password-based auth path — it proves email ownership, not credential validity. Ship as a separate endpoint (/account/request-unlock-token, /account/confirm-unlock-token) with its own rate-limit (per-email, not per-IP). Coordinate with Tweedledee on error responses and token validity window (recommend 15 minutes).

**Acceptance:**
- Email-based recovery token can be generated and validated independently of password auth
- Tokens expire after 15 minutes (or Queen-specified window)
- Email address on file must match the email used to request the token
- Successful token validation unlocks the account without re-checking the password
- Audit trail captures unlock-request timestamp, email verification timestamp, and unlock completion

**Risk:**

If the email address is stale or the user does not have access to the registered email, they are locked out permanently until support intervenes. Queen should rule on whether we offer fallback recovery (security questions, SMS, support ticket) or accept that email-only recovery is the constraint. Recommend Queen rule on this before the Tweedles start building.
