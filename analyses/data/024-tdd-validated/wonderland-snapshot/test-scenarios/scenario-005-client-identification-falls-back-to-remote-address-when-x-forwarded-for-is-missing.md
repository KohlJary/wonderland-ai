## Scenario 005: Client identification falls back to remote address when X-Forwarded-For is missing

**Severity:** degradation

**Setup:**

Client makes requests with no X-Forwarded-For header. Backend has no trusted proxy config. Quota is 10 req/min.

**Trigger:**

Client makes 11 requests to POST /api/messages, none with X-Forwarded-For.

**Expected:**

Requests are identified by remote address (socket peer IP). Requests 1-10 return 200. Request 11 returns 429.

**Concern:**

If behavior on missing X-Forwarded-For is undefined (returns 400, drops request, uses placeholder), contract-002 is broken. Frontend doesn't know if 429 is due to actual quota exhaustion or malformed request. Degradation: system works but fallback behavior is not documented.

**Property:**

For all requests with no X-Forwarded-For header, client_id = remote_address.

**Implies:**
- Implies contract-002 must specify explicit fallback before frontend can rely on consistent 429 behavior.
