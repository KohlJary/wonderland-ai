## Ticket 012: Cheshire Cat: confirm architectural deferral or v1 fix for distributed-IP credential-stuffing bypass

**Sources:** concern from Rabbit on distributed-IP bypass risk, scenario from Hatter: silent-wrongness-rate-limit-bypass-via-distributed-attack-across-many-ips-on-same-email
**Owner:** Cheshire Cat
**Tier:** v1
**Estimate:** 1-2 hours, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: implement-per-ip-rate-limiting-on-login-endpoint-per-queen-s-ruling

**Description:**

The current rate-limiting proposal uses per-IP limiting as the primary attack defense, with per-email lockout as the catch-all. Hatter's scenario 4 surfaces a known gap: distributed attacks (same email, many IPs) are correctly caught by per-email lockout, but the per-IP limit does nothing to slow them. Queen's ruling does not address email-based rate-limiting; only per-IP. Determine: (a) is per-email rate-limiting in scope for v1, or is it explicitly deferred as post-incident hardening? (b) if deferred, how should the team document this as a known gap? (c) if in scope, what does the architectural surface look like (shared cache with per-IP, separate policy, hybrid)? Surface your recommendation as a proposal or a deference to Queen for ruling on scope inclusion.

**Acceptance:**
- Architectural recommendation surfaces: per-email limiting in v1 (and shape), or explicitly deferred (and documented as known gap)
- If in-scope for v1: surface as proposal with implementation surface implications for Tweedles
- If deferred: document as post-incident hardening with rationale

**Risk:**

If per-email limiting is implicitly assumed but not architected, Tweedles will guess at implementation. If it's deferred without documentation, the team may ship v1 and forget the gap exists.
