## Ticket 012: Rate-limit account-unlock attempts to prevent unlock-path abuse during or after attack

**Sources:** test_scenario slug=high-volume-login-attempts-from-single-ip-across-distinct-usernames-triggers-rate-limit-before-lockout-threshold-is-crossed, adr slug=decouple-unlock-authorization-from-initial-authentication
**Owner:** tweedledum
**Tier:** fast-follow
**Estimate:** 1-2 hours, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: implement-account-recovery-primitive-validate-email-ownership-for-unlock-authorization
- Soft: monitoring-detect-high-volume-login-attempts-from-single-ip-across-distinct-usernames

**Description:**

Add rate-limiting to the unlock-request path (/account/request-unlock-token). Attacker could use the unlock flow as a secondary attack surface if rate-limits are absent. Rate-limit by email (max 3 unlock requests per hour per email), not by IP, because legitimate users may share IPs and we want to prevent unlock-request flooding without collateral damage. Pair with Dormouse on monitoring (alert if unlock-request volume spikes, which signals either legit user frustration or new attack vector). Fast-follow — ship after the immediate unlock path is live and we have real-world telemetry on unlock-request volume.

**Acceptance:**
- Unlock-request endpoint enforces max 3 requests per email per hour
- Requests beyond threshold return 429 with retry-after header
- Rate-limit counters are tracked in the session/recovery service, not by IP
- Audit trail logs every unlock request and every rate-limit rejection

**Risk:**

If rate-limit threshold is too aggressive, legitimate users who forget their password multiple times will be locked out of unlock. Too lenient, and the unlock path becomes a DoS vector. Recommend Dormouse observes unlock-request volume for 24 hours post-incident before finalizing the threshold, but ship a sensible default (3/hour) immediately.
