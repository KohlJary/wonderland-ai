## Ticket 005: Implement account unlock workflow for rate-limited users (email + link or SMS)

**Sources:** story:affected-user-can-regain-access-without-waiting-forever-or-jumping-through-chaos, story:user-locked-out-can-unlock-without-support-friction-if-they-own-the-account
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1–2 days, 60% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket:implement-rate-limiting-on-login-endpoint-per-queen-ruling
- Soft: question:cat-visibility-surface

**Description:**

Users locked out by the rate-limit need a self-service path to regain access without waiting for support or for a fixed timeout. Implement an unlock workflow that:
1. Generates a time-limited unlock token (valid for 30 minutes or per the Queen's ruling)
2. Sends the token via email (or SMS if available) to the account's registered contact
3. Validates the token on /unlock endpoint; on success, resets the lockout state and allows login
4. Logs the unlock event for audit trail and breach-analysis purposes

The workflow assumes the user can receive email/SMS at their registered address (i.e., they own the account). Alice's story: 'User locked out can unlock without support friction if they own the account'.

This depends on the Cat's visibility-surface answer: if successful auth during the attack exposed the account, we may need to force a session revocation or password reset as part of unlock. Confirm the visibility surface before finalizing the unlock logic.

**Acceptance:**
- Unlock token generated and stored server-side with 30-minute TTL (or per Queen ruling)
- Email sent to account's registered email with unlock link
- GET /unlock?token=<token> displays a confirmation page with account identifier
- POST /unlock with valid token resets lockout_attempts to 0, logs unlock event, allows next login
- Invalid/expired tokens reject gracefully with clear messaging
- Unlock event logged with timestamp, account ID, token hash (not plaintext)

**Risk:**

Email delivery latency may make this feel slow to users (could take 5–10 minutes to arrive). If this is unacceptable, we may need SMS as a faster path. Also: if the Cat confirms successful auth exposed the account, this ticket may need to add a password-reset flow as a prerequisite to unlock, which expands scope significantly. Confirm visibility before committing.
