## Scenario 015: Rate limiter and lockout use in-memory state in service.py but are supposed to be durable per Queen ruling — no database persistence

**Severity:** breakage

**Setup:**

service.py instantiates `self.rate_limiter = RateLimiter(requests_per_minute=10)` and `self.account_lockout = AccountLockout(failure_threshold=5)`. These are passed to the constructor. The rate_limit.py file defines `RateLimiter` which takes a `db_session_factory` and queries the `FailedAttempt` table. But service.py's constructors use positional args `requests_per_minute=10` and `failure_threshold=5`, which don't match the `RateLimiter.__init__` signature in rate_limit.py.

**Trigger:**

Instantiation of `AuthService(db_session_factory)` without explicit rate limiter/lockout objects.

**Expected:**

The default rate limiter and lockout are created with sensible defaults; they query the FailedAttempt table for durability; the service works correctly across restarts.

**Concern:**

The constructor signatures don't match. `RateLimiter.__init__` expects `db_session_factory`; `AuthService` tries to instantiate `RateLimiter(requests_per_minute=10)`. This is a type mismatch that will fail at runtime.

**Property:**

For all rate-limiting and lockout state, the implementation must be durable (backed by the database), not in-memory, so that service restarts during an active attack do not lose state.

**Implies:**
- Implies that rate_limit.py and service.py were written to different contracts. One expects in-memory state (service.py's constructor args), the other expects database-backed state (rate_limit.py's implementation). This is a unification failure.
- The Queen's ruling requires durable state. The current code has the database-backed implementation in rate_limit.py, but service.py doesn't know how to instantiate it correctly.
