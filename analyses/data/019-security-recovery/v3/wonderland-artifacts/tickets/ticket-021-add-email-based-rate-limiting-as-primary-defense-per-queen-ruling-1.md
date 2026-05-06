## Ticket 021: Add email-based rate-limiting as primary defense per Queen ruling #1

**Sources:** ruling-distributed-ip-credential-stuffing-bypass-email-based-rate-limiting-required
**Owner:** Tweedledee / Tweedledum
**Tier:** v1
**Estimate:** 2–3 days, 50% confident
**Status:** open

**Dependencies:**
- Blocks: implementation-merge-gate
- Blocked by: —
- Soft: —

**Description:**

The Queen ruled that distributed-IP credential-stuffing attacks require email-based rate-limiting as an *active* defense, not just per-email lockout as a passive catch-all. The current implementation has IP-based rate limiting (10 req/min) as secondary friction and per-email lockout (5 failures) as the primary catch-all. This is incomplete. Add email-based rate-limiting: per-email sliding window (e.g., 50 login attempts per hour), checked before lockout, returning 429 if exceeded. Compose with existing per-IP limit such that: (1) an attacker on a single IP hitting a single email hits the email limit first, (2) an attacker on many IPs hitting the same email still hits the email limit, (3) operators can tune both limits independently. Update src/auth/rate_limit.py with email-based logic; update tests to cover distributed-IP scenarios (Hatter scenario #4). Do not ship without this; the Queen's ruling is explicit.

**Acceptance:**
- Email-based rate limiter returns 429 when email exceeds per-hour threshold
- Per-IP and per-email limits are independent (hitting one does not advance the other)
- Test coverage includes distributed-IP attack scenario (many IPs, single email target)
- Both limits are observable via instrumentation hooks (same contract as ticket above)

**Risk:**

Adding email-based limiting may increase memory footprint if email space is high-cardinality. Dormouse should confirm TTL/eviction semantics are acceptable for production.
