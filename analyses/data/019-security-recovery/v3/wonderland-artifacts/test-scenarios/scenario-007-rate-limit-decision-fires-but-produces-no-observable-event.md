## Scenario 007: Rate-limit decision fires but produces no observable event

**Severity:** silent-wrongness

**Setup:**

AuthService initialized with rate limiter (10 req/min). Single IP makes 11 requests in 1 minute. The 11th request violates the rate limit and returns 429.

**Trigger:**

10th and 11th login attempt from same IP within the same minute window.

**Expected:**

The 11th attempt is rejected with 'rate_limited' reason. A metric or event is emitted to production telemetry (e.g., 'auth.rate_limit_exceeded' counter, tagged with source_ip and timestamp).

**Concern:**

The current implementation raises RateLimitViolation internally and returns reason='rate_limited', but does not emit any observable signal. Production has no way to detect that rate-limiting is happening. Dormouse cannot build a metric on 'how many rate-limit decisions per IP per window' without adding instrumentation to the RateLimiter class.

**Property:**

For all rate-limit violations R, there exists an observable event E such that E records (source_ip, timestamp, window_name) and can be aggregated into a metric.

**Implies:**
- Requires instrumentation hook in RateLimiter.check() to emit events when violations occur.
- Dormouse owns the contract for what fields and cardinality bounds the event must have.
