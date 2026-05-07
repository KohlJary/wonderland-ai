## Implementation 001: Caterpillar findings addressed: constants export, public reset(), fallback documentation

**Side:** backend
**Ticket:** none — response to review feedback
**Contract:** message-envelope v3 — unchanged; the rate limiter contract is unchanged, only implementation clarity improves
**Ready for review:** no

**Approach:**

Three targeted improvements per code review: (1) QUOTA_LIMIT and QUOTA_WINDOW_SECONDS moved to module-level constants and imported by api/messages.py to ensure single source of truth. (2) RateLimiter.reset() public method added and called by test fixture, replacing private attribute mutation. (3) Fallback client_id derivation now has a detailed comment explaining the defensive 'unknown' bucket behavior.

**Invariants Enforced:**
- Rate limit quota is 10 requests/minute: now enforced from a single module-level constant
- Unidentifiable clients are rate-limited collectively under 'unknown' bucket: defensive behavior now explicitly documented

**Failure Modes Handled:**
- Proxy misconfiguration or malformed requests: fallback to 'unknown' client_id bucket with documented behavior

**Files:**
- src/backend/rate_limiter.py: Moved QUOTA_LIMIT and QUOTA_WINDOW_SECONDS to module level (lines 16-17); added public reset() method (lines 41-44); updated internal code to reference module-level constants
- src/backend/api/messages.py: Import QUOTA_LIMIT and QUOTA_WINDOW_SECONDS; use QUOTA_LIMIT dynamically in 429 response body and docstring
- tests/conftest.py: Call _rate_limiter.reset() instead of directly mutating private attributes
