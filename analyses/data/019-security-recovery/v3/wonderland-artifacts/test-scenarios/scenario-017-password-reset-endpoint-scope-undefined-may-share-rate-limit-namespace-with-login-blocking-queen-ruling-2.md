## Scenario 017: Password-reset endpoint scope undefined — may share rate-limit namespace with login, blocking Queen ruling #2

**Severity:** degradation

**Setup:**

The Queen's ruling #2 requires that password-reset flows must not be blocked by the per-email lockout (so users locked by attack can recover). Currently, /password-reset endpoint does not exist. When it is implemented, the rate-limit policy is undefined: will it share the same per-email counter as /login, or have separate limits?

**Trigger:**

A user's account is locked (15 failures in 30 min). The user attempts to reset their password via /password-reset?email=user@example.com to self-recover.

**Expected:**

The password-reset endpoint either (a) has its own rate limit (separate from login), or (b) is explicitly exempt from per-email rate limiting. The user can initiate password reset even though their account is locked from failed logins.

**Concern:**

If password-reset shares the per-email rate limit with login, the locked user cannot reset—they hit the same per-email lockout that's preventing login. If password-reset has no rate limiting at all, it becomes a secondary attack vector (reset-spam + account takeover). The contract must be explicit now, before implementation.

**Property:**

For all authenticated endpoints, rate-limit policies must be explicit: shared namespace, separate namespace, or exempt. The policy must support the Queen's rulings without creating secondary attack vectors.

**Implies:**
- Implies that /password-reset is a future story, not yet implemented. The Hatter's scenarios and Queen's rulings surface a dependency: the rate-limit namespace design must account for password-reset before it's added. Defer password-reset v1 until the contract is written.
- Implies a design decision for the Cat: do per-email rate limits apply across all endpoints, or per-endpoint? The answer shapes whether password-reset needs special handling.
