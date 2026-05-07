## Scenario 010: Missing or unidentifiable client ID triggers documented fallback behavior

**Severity:** degradation

**Setup:**

Client makes request in edge case: reverse proxy strips X-Forwarded-For, remote address is unavailable (contrived). Backend config does not specify fallback.

**Trigger:**

POST /api/messages with no identifiable client.

**Expected:**

Backend either (A) returns 400 Bad Request with clear reason, or (B) uses documented fallback (e.g., client_id='anonymous'). Behavior is consistent and documented. If fallback is used, all 'anonymous' clients share same quota bucket.

**Concern:**

If behavior is undefined, frontend gets inconsistent errors (sometimes 429, sometimes 400, sometimes 200 with duplicates). Contract-002 explicitly asks for this specification. Degradation: system works but contract is incomplete.

**Property:**

For all requests with no identifiable client, client_id is determined by documented fallback rule, consistently applied.

**Implies:**
- Implies contract-002 must be finalized with explicit fallback before Tweedles ship enforcement code.
