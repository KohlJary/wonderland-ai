## Scenario 014: Rate limiter returns RateLimitResult but service.py expects RateLimitViolation exceptions — exception handling contract mismatch

**Severity:** breakage

**Setup:**

Assuming the import errors are fixed and `RateLimiter.check()` is called from `service.login()`. The rate_limit.py implementation returns `RateLimitResult(status=RateLimitStatus.IP_THROTTLED)` on rate limit hit. The service.py code wraps the call in `try: self.rate_limiter.check(source_ip) except RateLimitViolation as e:`.

**Trigger:**

A login attempt from an IP that has exceeded the rate limit threshold.

**Expected:**

The rate limiter raises a `RateLimitViolation` exception; the exception is caught; the service returns `LoginResult(ok=False, reason='rate_limited', retry_after_seconds=...)` to the caller.

**Concern:**

`RateLimitResult` is a return value, not an exception. The try/except block will never catch anything; the check() call will return normally with `status=IP_THROTTLED`, but service.py doesn't check the result—it just returns the result object as a response, or ignores it. The logic never reaches the `except` block.

**Property:**

For all control-flow paths in rate limiting, the service must distinguish between allowed/throttled/locked states and handle each appropriately before continuing.

**Implies:**
- Implies that the contract between rate_limit.py and service.py is broken. Both cannot ship in this state; one must change to match the other. This is load-bearing for the Queen's rate-limiting ruling.
- Implies an architectural decision: does the rate limiter communicate via exceptions (raise RateLimitViolation) or via return-value status (return RateLimitResult)? The team chose return-value in rate_limit.py; service.py must be updated to check the result.
