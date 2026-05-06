## Ticket 013: Password-reset endpoint design contract: rate-limit isolation required in v1

**Sources:** ADR: Auth defense-in-depth; scenario 5 (lockout-escape-hatch)
**Owner:** Cheshire Cat
**Tier:** fast-follow
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: ticket #11 (observability contract) — the reset-flow observability should be specified alongside login/lockout observability

**Description:**

Password-reset endpoint does not exist in v1 mitigation scope (confirmed by Tweedles in ticket #9). When /password-reset ships in fast-follow, it must have explicit rate-limit isolation: email-address lookups in the reset flow must bypass the per-IP rate limiter, and reset-initiation must have its own rate-limit policy to prevent reset-spam attacks. Design the contract now so implementation does not ship with implicit assumptions about rate-limit namespace sharing. Output: design document or ADR clarifying reset-flow rate-limit isolation, with test scenarios that specify the expected behavior.

**Acceptance:**
- Design document specifies rate-limit policies for /password-reset email lookup, initiation, and completion
- Document clarifies relationship between reset-flow rate limits and login-flow rate limits (separate namespace vs. shared vs. conditional)
- Test scenarios for reset flow + lockout interaction are documented (e.g., locked user can initiate reset without hitting rate limit)

**Risk:**

If reset-flow rate-limit isolation is not designed early, fast-follow implementation may inherit the login-flow rate-limiting logic and accidentally lockout users attempting recovery.
