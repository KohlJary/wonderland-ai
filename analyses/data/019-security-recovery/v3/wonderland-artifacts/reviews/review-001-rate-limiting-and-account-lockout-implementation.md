## Review 001: Rate-limiting and account-lockout implementation

**Files reviewed:** src/auth/rate_limit.py, src/auth/service.py, src/auth/endpoints.py, tests/test_auth.py
**Verdict:** request-changes

### Findings

#### block: Endpoint returns wrong HTTP status code for rate-limited/locked requests
**Location:** src/auth/endpoints.py:45-52
**Quote:**

```
if not result.ok:
            # Single failure message regardless of reason — don't leak
            # whether the email exists.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid email or password",
            )
```

**Read:** The endpoint treats all login failures identically, returning 401 (Unauthorized) whether the failure is a credential mismatch or a rate-limit/lockout violation. This is incorrect semantics: rate-limited and account-locked responses should return 429 (Too Many Requests) per RFC 6585, with a Retry-After header.
**Concern:** Clients that implement retry logic will interpret 401 as 'credentials rejected' (no-retry), not 'temporarily unavailable' (retry). This breaks the rate-limit control's ability to signal backoff to legitimate clients. Attackers will see 401 and continue the attack without backoff pressure.
**Request:** Modify the endpoint to inspect result.reason and return 429 with Retry-After when the reason is 'rate_limited' or 'account_locked'. Keep 401 for 'unknown_email' and 'invalid_password'. This requires LoginResult to carry the retry_after_seconds from RateLimitViolation.

#### block: Rate-limit failures are not logged
**Location:** src/auth/service.py:72-79
**Quote:**

```
try:
            self.rate_limiter.check(source_ip)
        except RateLimitViolation:
            self._log_failure(
                None, normalized_email, "rate_limited", source_ip, user_agent
            )
            return LoginResult(ok=False, reason="rate_limited")
```

**Read:** When a rate-limit violation is caught, the code calls `_log_failure(db=None, ...)`. The `_log_failure` method then early-returns without logging because db is None. This means rate-limited requests (the attack signature) are never recorded in the FailedAttempt table.
**Concern:** Without logs, forensics and incident analysis are blind: 'how many attackers hit us?', 'which IPs?', 'how long did the attack last?' cannot be answered. The Dormouse's future observations will be incomplete.
**Request:** Modify _log_failure to accept db_session_factory as an argument (passed from __init__), so it can create a new session for the log write when called from the rate-limit check. Alternatively, pass db as a context manager context that handles the session lifecycle. Test that rate-limit failures are logged to FailedAttempt.

#### block: Missing test coverage for rate-limiting and account-lockout scenarios
**Location:** tests/test_auth.py:1-80
**Quote:**

```
# Note: there is intentionally no test_login_rate_limited test, because
# /login has no rate limit yet. See #ENG-471 for the deferred work.
```

**Read:** The test file acknowledges the absence of rate-limit and lockout tests. All six of the Hatter's test scenarios (credential-stuffing from single IP, account lockout, false positives on shared IPs, distributed attack on same email, password-reset escape hatch, monitoring) are currently untested.
**Concern:** Without tests, future code changes can silently break the rate-limit logic, and the Hatter's scenarios go unverified. The incident mitigation is ship-first but test-never is not acceptable; tests must land before merge to lock in the behavior.
**Request:** Add tests to tests/test_auth.py covering at minimum: (1) IP rate-limit after threshold; (2) account lockout after 5 failed attempts; (3) recovery on successful login; (4) simultaneous IP rate-limit and account lockout states. Use the Hatter's scenario titles as test names.

#### change-required: Endpoint does not signal Retry-After to rate-limited clients
**Location:** src/auth/endpoints.py:45-52
**Quote:**

```
raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid email or password",
            )
```

**Read:** When returning a 429, the endpoint should include a Retry-After header (seconds until the rate limit expires). RateLimitViolation carries retry_after_seconds, but it's lost after the except clause.
**Concern:** Clients won't know how long to wait before retrying. Without the header, they either retry too quickly (hammering the limit again) or give up entirely.
**Request:** Capture the retry_after_seconds from RateLimitViolation in the LoginResult dataclass, then add headers={'Retry-After': str(retry_after_seconds)} to the HTTPException when returning 429.

#### suggestion: Password-reset flow is not exempted from rate limiting
**Location:** src/auth/endpoints.py
**Quote:**

```
[no explicit password-reset endpoint shown]
```

**Read:** The Hatter's scenario 'Lockout escape hatch — legitimate password-reset flow must not be rate-limited' suggests a password-reset endpoint (e.g., POST /auth/password-reset) that should not be subject to the IP rate limit, because users who are locked out need a way to recover without needing to guess their password 4 more times.
**Concern:** If password-reset is subject to the same IP rate limit as /login, a locked-out user on a shared IP (e.g., corporate network) cannot reset their password. The feature exists but is unusable.
**Request:** Add a password-reset endpoint (or clarify if one exists elsewhere) that calls AuthService without triggering the rate limiter, or add an optional bypass parameter to the rate limiter. Flag this to the Cat for architectural guidance on escape-hatch design.

#### suggestion: No observable logging of rate-limit and lockout events for production monitoring
**Location:** src/auth/rate_limit.py, src/auth/service.py
**Quote:**

```
[RateLimiter and AccountLockout have no logging statements]
```

**Read:** The Hatter's scenario 'Monitoring gap — rate-limit and lockout events should be observable in production' indicates that production monitoring should see these events. Currently, rate-limit and lockout checks are silent; they don't emit structured log entries that a monitoring system can ingest.
**Concern:** The Dormouse will not be able to detect patterns like 'lockout rate is increasing' or 'new attack wave from IP range X'. Without observability, the system is flying blind.
**Request:** Add logging (via Python logging module or a metrics library) at key points: when an IP hits the rate limit, when an account is locked, when an account is unlocked (successful login). These should be structured logs (JSON) with fields like ip, email, threshold_exceeded, window_expires_at, etc. This is a suggestion rather than block because the immediate incident response may not require it; it's a hardening concern for production durability.

#### note: In-memory cache is documented but not technically hardened
**Location:** src/auth/rate_limit.py:1-12
**Quote:**

```
Both use in-memory caches with TTL-based expiry to avoid DB load
during high-volume attacks. State is NOT persisted across restarts,
which is acceptable for SIGv1 incident response (this rate limiter
is designed to stop the current attack, not to be infinitely durable).

For production hardening, migrate these to Redis or a distributed cache.
```

**Read:** The comments correctly identify the in-memory cache as a temporary measure and call out the path to production (Redis migration). This is appropriate for incident response.
**Concern:** None for incident response; this is a known-and-acceptable limitation. On next heartbeat, file a ticket for Redis integration.
**Request:** No change required. For awareness: the Rabbit should file a post-incident ticket to migrate to Redis/Memcached before the next attack window.

#### note: RateLimitViolation exception structure is sound
**Location:** src/auth/rate_limit.py:19-26
**Quote:**

```
class RateLimitViolation(Exception):
    """Raised when a request violates the rate limit or lockout policy."""

    def __init__(self, reason: str, retry_after_seconds: int | None = None):
        self.reason = reason
        self.retry_after_seconds = retry_after_seconds
```

**Read:** The exception carries both a reason and a retry_after_seconds hint, which is correct. The service layer catches it and translates it to a LoginResult reason.
**Concern:** None.
**Request:** No change required. This is well-designed.

### Approvals

- The core rate-limiting logic in RateLimiter is well-structured: sliding window with clear expiry semantics, configurable limits, clean API. The test of the algorithm (checking count against threshold, resetting on window expiry) is straightforward and the implementation is correct.
- The account-lockout logic in AccountLockout correctly handles the case where a lockout is already active (doesn't stack further failures, doesn't bump the locked_until time). This prevents attack amplification.
- Integration with AuthService is clean: rate limit and lockout checks happen before any DB access, which is the right performance boundary. Failure counters are only incremented on actual credential failure, not on rate-limit rejection.
- The dataclass structure of LoginResult correctly captures all the information the endpoint needs (ok, reason, session). The existing separation of 'rate_limited'/'account_locked' from 'unknown_email'/'invalid_password' is correct and should be preserved.

### Cross-domain references

- The password-reset escape hatch (Hatter scenario) and monitoring gap (Hatter scenario) are both addressed in the findings. These should be confirmed with the Queen's ruling on whether they are production requirements or incident-only scope.
- The endpoint's HTTP semantics (429 vs 401) may have API design implications for the Cat; confirm the distinction is intentional.
- The Dormouse will need to be asked whether the absence of structured logging for rate-limit events is acceptable for incident response, or if it blocks observability of the attack.
