## Ticket 017: User messaging for rate-limiting on shared IP during credential-stuffing attack

**Sources:** story: legitimate-user-on-shared-ip-experiences-rate-limiting-during-credential-stuffing-attack-needs-to-understand-it-s-temporary
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 0.5–1 day, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket: implement-per-ip-rate-limiting-on-login-endpoint-per-queen-s-ruling
- Soft: ticket: implement-rate-limit-and-lockout-observability-metrics-events-for-breach-notification-determination

**Description:**

When a legitimate user on a shared IP (corporate network, university, coffee shop) hits the per-IP rate limit (10 requests/minute) during the credential-stuffing attack, they receive a 429 HTTP response. This response must include a clear message explaining: (1) the service is under attack and has temporarily rate-limited your IP address, (2) this is not a problem with your account, (3) the rate limit will clear in approximately 1 minute (or show the exact retry-after window), (4) what to do if they cannot log in after waiting. Success: user sees the message, understands it's temporary and not their fault, waits 60 seconds, and logs in. Failure: user sees a generic 429 error, assumes the service is broken, leaves, and never comes back.

**Acceptance:**
- 429 Too Many Requests response includes human-readable body explaining rate-limiting is due to attack, not user error
- Response includes Retry-After header with seconds to wait (recommend 60s for 10 req/min window)
- Message is tested with users who have experienced real rate-limiting (or close simulation) to confirm clarity
- If user on shared IP is rate-limited, they can navigate to a status page or support documentation without needing to log in

**Risk:**

If the rate-limit message is unclear or missing, users on shared IPs will perceive the service as broken during the attack. The attack mitigation will have prevented the attacker but driven away legitimate users. The 429 response is the first and only signal the user sees; it must be clear.
