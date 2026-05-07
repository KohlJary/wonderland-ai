## Scenario 001: Client exceeds quota and receives 429 with Retry-After header

**Severity:** breakage

**Setup:**

Rate limiter configured for 10 requests/minute. Client has 0 requests in current bucket. Client makes 11 consecutive POST /api/messages requests.

**Trigger:**

The 11th POST /api/messages request arrives within the same 60-second window.

**Expected:**

Requests 1-10 return 200. Request 11 returns 429 with HTTP status code 429. Response includes Retry-After header with integer value (seconds until bucket resets). Response includes X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers.

**Concern:**

Without 429 status, client doesn't know it's rate-limited vs. experiencing network error. Without Retry-After header, frontend can't render countdown timer. Silent failure: if backend returns 200 on 11th request, enforcement is broken and user will see duplicate messages.

**Property:**

For all client C and window W, if request_count(C, W) > quota, the first request exceeding quota returns 429 with Retry-After > 0.

**Implies:**
- Implies enforcement middleware must fire before message handler — backend architecture decision.
- Implies response schema: contract-004 specifies JSON body shape — frontend needs exact field names.
