## Ticket 014: Implement rate-limiting on /login endpoint per Queen ruling

**Sources:** ruling/rate-limit-login-endpoint-to-halt-credential-stuffing-attack
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1.5-2 hours, 70% confident
**Status:** open

**Dependencies:**
- Blocks: investigate-whether-any-of-the-4127-attempted-credentials-succeeded-parse-audit-trail-for-successful-logins
- Blocked by: —
- Soft: extend-user-account-lockout-threshold-from-5-to-10-failed-attempts-effective-immediately

**Description:**

Implement rate-limit enforcement on the /login endpoint per Queen ruling 001-rate-limit-login-endpoint-to-halt-credential-stuffing-attack. Scope: (1) rate-limit by source IP: 10 attempts per 60 seconds; (2) rate-limit by username: 5 attempts per 60 seconds; (3) return HTTP 429 (Too Many Requests) when either threshold is exceeded; (4) log every rate-limit trigger event to audit_trail with (source_ip, username, timestamp, threshold_type). The Dormouse and Caterpillar will need this audit trail to investigate breach scope (ruling 002). Do not implement session-layer access gating yet — that is architectural (Cat's domain) and does not block the rate-limit from shipping.

**Acceptance:**
- Rate-limit middleware is integrated into http_middleware.py before /login endpoint handler
- IP-based rate-limit: 10 attempts per 60 seconds per source IP; subsequent attempts return 429
- Username-based rate-limit: 5 attempts per 60 seconds per username; subsequent attempts return 429
- Every rate-limit trigger is logged to audit_trail with (source_ip, username, timestamp, threshold_type)
- Test: simulate attack pattern from 203.0.113.42 across 2,803 usernames; verify rate-limit triggers within 10 attempts and returns 429

**Risk:**

Performance impact if rate-limit checks are implemented naively (e.g., scanning all prior attempts on every request instead of using a rolling-window counter). Mitigate by using a simple in-memory counter (dict keyed by (source_ip, timestamp_bucket)) with periodic cleanup. If this impacts login latency measurably, the Dormouse will report it and we iterate.
