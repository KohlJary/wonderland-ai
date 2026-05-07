## Ticket 001: Implement rate limiting enforcement with header validation

**Sources:** attacker-cannot-bypass-rate-limiting-by-spoofing-headers
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 2–3 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: user-discovers-rate-limit-messaging, operator-rate-limit-observability
- Blocked by: —
- Soft: —

**Description:**

Build the rate-limiting middleware that enforces per-user/per-IP quotas and rejects requests exceeding limits. Must validate rate-limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset) and reject spoofed headers by re-deriving from server-side state. Return 429 with Retry-After. Do not implement operator dashboards or user-facing messaging in this ticket — those are follow-ups.

**Acceptance:**
- Rate limiting rejects requests over quota and returns 429
- Spoofed rate-limit headers are ignored; server-side state is authoritative
- Retry-After header is present and accurate in 429 responses
- Per-user quotas are tracked; per-IP fallback exists for unauthenticated requests

**Risk:**

Determining the right quota semantics (per-second vs. per-minute, burst allowance) may require clarification from Alice on the 'rapid messages' story. Expand to 3.5 days if auth integration requires session middleware changes.
