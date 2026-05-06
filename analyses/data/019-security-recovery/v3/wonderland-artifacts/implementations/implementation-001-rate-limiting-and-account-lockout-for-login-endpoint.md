## Implementation 001: Rate limiting and account lockout for /login endpoint

**Side:** backend
**Ticket:** #ENG-471 / incident-response
**Contract:** No contract change — this is a defensive layer added to the existing /login endpoint. AuthService.login signature unchanged; LoginResult.reason field extended with 'rate_limited' and 'account_locked' values.
**Ready for review:** yes

**Approach:**

Added RateLimiter (IP-based, sliding 1-min window) and AccountLockout (threshold-based, per email) classes to src/auth/rate_limit.py. Both use in-memory caches with TTL. AuthService now instantiates both by default (10 req/min, 5-attempt lockout) and checks them early in login() before credential verification. Rate-limited requests return 429; locked accounts return 423. Successful login resets the per-email failure counter.

**Files:**
- src/auth/rate_limit.py: new RateLimiter and AccountLockout classes with sliding-window and threshold logic
- src/auth/service.py: added rate_limiter and account_lockout attributes; checks in login() before credential verification
- src/auth/endpoints.py: updated /login error handler to return 429 (rate_limited) and 423 (account_locked) status codes
- tests/test_auth.py: added 8 new test cases covering rate limit, lockout, and interaction scenarios

**Known Limitations:**
- In-memory caches not persisted across service restarts — acceptable for incident response; migrate to Redis/Memcached for production.
- Rate-limit and lockout events logged as failed attempts but not instrumented for monitoring/alerting — Dormouse surface needed.
- No admin API for manual unlock/reset — would need separate endpoint for incident remediation.
- Lockout duration defaults to None (permanent until manual reset) — auto-recovery via timedelta() parameter but not used by default.
