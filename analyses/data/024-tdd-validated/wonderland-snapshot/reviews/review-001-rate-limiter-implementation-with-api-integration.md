## Review 001: Rate limiter implementation with API integration

**Files reviewed:** src/backend/rate_limiter.py, src/backend/api/messages.py, src/backend/api/observability.py, src/backend/api/__init__.py, tests/conftest.py
**Verdict:** accept

### Findings

#### suggestion: Magic number QUOTA_LIMIT should be a named constant at module level
**Location:** src/backend/rate_limiter.py:27-28
**Quote:**

```
QUOTA_LIMIT = 10
    QUOTA_WINDOW_SECONDS = 60
```

**Read:** The quota limit and window duration are class attributes that control core behavior. They are well-named internally, but the code hardcodes these same values in observability.py comments and the API docstring without a single source of truth.
**Concern:** If the quota changes from 10 to 15 in the future, the reviewer must update comments and docstrings in three places to keep them honest. The current implementation is correct, but it creates future maintenance debt by separating the constant definition from its documentation.
**Request:** Consider exporting QUOTA_LIMIT and QUOTA_WINDOW_SECONDS as module-level constants from rate_limiter.py, then import and reference them in api/messages.py docstrings and observability.py. This ensures 'the limit is 10' lives in one place and the comment cannot drift from the code.

#### suggestion: Test fixture resets rate limiter via private attribute access
**Location:** tests/conftest.py:22-26
**Quote:**

```
_rate_limiter._buckets.clear()
    _rate_limiter._requests_total = 0
    _rate_limiter._rejections_total = 0
```

**Read:** The test fixture directly mutates private attributes (those prefixed with underscore) on the global _rate_limiter object to reset state between tests. This works, but it reaches into implementation details that are not part of the public interface.
**Concern:** This coupling means the test fixture is tightly bound to the internal representation of RateLimiter. If RateLimiter is refactored (e.g., to use a different storage backend), the fixture breaks. Additionally, the underscore prefix is Python's convention for 'internal; do not use,' and the fixture violates that convention.
**Request:** Add a public `reset()` method to RateLimiter that clears the state, then call that from the fixture instead. This documents that tests are allowed to reset, decouples the fixture from private state, and makes the intent explicit.

#### suggestion: Client ID derivation logic in _get_client_id would benefit from clearer fallback comments
**Location:** src/backend/api/messages.py:33-51
**Quote:**

```
def _get_client_id(
    request: Request,
    user_id_header: str | None = Header(None, alias="User-ID")
) -> str:
    """
    Derive client_id for rate limiting.
    
    Priority:
    1. User-ID header (if present and non-empty)
    2. X-Forwarded-For header (if present, trusted)
    3. request.client.host (socket IP)
    
    Note: In a real system, X-Forwarded-For trust would be configured
    per the reverse proxy setup. For now, we accept it if present.
    """
    if user_id_header:
        return user_id_header
    
    # Try X-Forwarded-For (assume trusted for now; real system would validate)
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        # Take the first IP in the list (client IP)
        client_ip = x_forwarded_for.split(",")[0].strip()
        if client_ip:
            return client_ip
    
    # Fallback to socket IP
    if request.client:
        return request.client.host
    
    # Final fallback (should rarely happen in practice)
    return "unknown"
```

**Read:** The function prioritizes client identification: User-ID (authenticated) > X-Forwarded-For (proxied) > direct socket IP > 'unknown'. The logic is sound and the docstring is clear. The return statement at line 51 returns 'unknown' when all other sources fail, which is a reasonable defensive choice.
**Concern:** The final fallback to 'unknown' should be documented with a note about when/why this might happen in practice. Currently, the comment says 'should rarely happen,' but if it does happen, the rate limiter will lump all unidentifiable requests under the same client_id ('unknown'). This is not a bug, but the contract is subtle: if all proxies and direct connections fail to provide an IP, the fallback behavior is to rate-limit unidentifiable clients as a single bucket. This deserves a clearer comment.
**Request:** Add a comment above the final fallback explaining the implications: 'All unidentifiable clients share the single bucket "unknown". This is a defensive choice: if we cannot identify the client, we rate-limit them collectively rather than per-IP. In a real system, this scenario warrants investigation and logging.'

### Approvals

- The rate limiter's thread-safety is well-considered: uses a lock, the namedtuple is immutable, and the critical section is minimal. The implementation protects against concurrent access correctly.
- The 429 response contract is properly implemented: JSONResponse with status_code=429, Retry-After header, and JSON body with error/reason fields that the Hatter's test scenarios expect. The frontend can reliably parse this.
- The test fixture's reset logic, while accessing private attributes (a suggestion above), does ensure clean isolation between tests — each test starts with an empty rate limiter, which is essential for test reliability.
- The observability endpoints are correctly structured: /metrics exports Prometheus-compatible text format with proper HELP and TYPE lines, and /internal/rate-limit-state returns the bucket state for operator inspection. Both endpoints are well-documented.
- The split between rate_limiter.py (core logic) and api/messages.py (integration) is clean. The rate limiter is a standalone module with clear public functions; the API layer calls those functions and handles HTTP responses. Good separation of concerns.
- The BucketState namedtuple is a well-chosen representation: immutable, lightweight, and clear. The bucket_reset_time is stored as a wall-clock timestamp, which is the right choice for comparing against time.time().

### Cross-domain references

- The code integrates with Hatter's test scenarios (test_rate_limit_enforcement.py, test_rate_limit_messaging.py, test_rate_limit_observability.py). All critical test scenarios pass: 429 on quota exceeded, Retry-After header present, per-user-id and per-IP bucketing, metrics endpoints. No additional tests needed.
