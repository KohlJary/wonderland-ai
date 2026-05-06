## Ticket 022: Define and document /password-reset rate-limit isolation contract per Queen ruling #2

**Sources:** ruling-password-reset-endpoint-must-have-separate-rate-limit-policy-from-login
**Owner:** Tweedledee / Tweedledum
**Tier:** v1
**Estimate:** 0.5 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: cheshire-cat-confirm-architectural-deferral-or-v1-fix-for-distributed-ip-credential-stuffing-bypass

**Description:**

The Queen ruled that password-reset endpoint 'must have separate rate-limit policy from login' and the current /password-reset does not exist in v1 scope. However, the rate-limit implementation in rate_limit.py must be architecturally scoped such that a future /password-reset can be isolated without refactoring. Review the rate_limit.py implementation and document (in code comments and in a contract note): (1) can /password-reset bypass the per-IP rate limiter entirely, or does it need its own per-IP limit? (2) can /password-reset use the same email-based limit as login (e.g., 50 attempts/hour), or must it have a separate namespace (e.g., 10 reset attempts/hour)? (3) if /password-reset is added to login.py flow, what changes are needed to rate_limit.py to support separate policies? Document the contract such that when /password-reset ships in fast-follow, the implementation can reference this contract and avoid refactoring.

**Acceptance:**
- rate_limit.py includes clear API for separate namespaces (e.g., 'reset_policy' parameter to RateLimiter, or separate RateLimiter instance for reset endpoint)
- Contract note exists documenting the decision: password-reset can/cannot share per-IP limits, can/cannot share per-email limits, and what code changes are needed if namespace isolation is required
- Contract note is reviewed and approved by the Caterpillar and the Cat before v1 ships

**Risk:**

If the rate_limit.py design does not support namespace isolation, this may force refactoring. Resolve now before the contract is locked.
