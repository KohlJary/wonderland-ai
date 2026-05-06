## Scenario 013: Implementation error: RateLimitViolation and AccountLockout classes do not exist — import will fail

**Severity:** breakage

**Setup:**

The code as shipped: service.py imports `from src.auth.rate_limit import AccountLockout, RateLimitViolation, RateLimiter`. The rate_limit.py file defines `RateLimiter` but not `AccountLockout` or `RateLimitViolation`.

**Trigger:**

Any attempt to import `AuthService` from `service.py` (e.g., test fixture, application startup).

**Expected:**

Imports succeed; AuthService instantiates with all three classes available.

**Concern:**

The imports will fail with `ImportError: cannot import name 'AccountLockout'` or similar. This prevents any test from running and any application from starting. The code cannot execute in this state.

**Property:**

For all agent-shipped code, all imports must resolve to classes/functions that exist in the codebase.

**Implies:**
- Implies that service.py is referencing a contract that rate_limit.py does not implement. The Caterpillar will flag this as a review blocker. Before the Tweedles resume, the two files must agree on the class hierarchy and exception semantics.
- Implies that the implementation is incomplete — either rate_limit.py is missing classes, or service.py is importing incorrectly. This is a synchronization failure in the Pair Protocol.
