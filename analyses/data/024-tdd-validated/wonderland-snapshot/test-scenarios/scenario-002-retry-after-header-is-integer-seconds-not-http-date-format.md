## Scenario 002: Retry-After header is integer seconds, not HTTP-date format

**Severity:** degradation

**Setup:**

Rate limiter configured for 10 req/min. Client has made 10 requests in current bucket (quota full).

**Trigger:**

Client sends 11th POST /api/messages at T=35 seconds into the bucket window (reset at T=60).

**Expected:**

Response includes Retry-After header with value 25 (60 - 35 = 25 seconds remaining).

**Concern:**

If Retry-After is HTTP-date format, frontend JavaScript Date.parse() requires timezone normalization. If decimal seconds or milliseconds, frontend countdown breaks silently. Silent-wrongness: both 200 and '429 with wrong format' look like responses; frontend has to guess which is correct.

**Property:**

For all bucket reset times R and current time T, Retry-After = max(0, R - T) as integer seconds.

**Implies:**
- Implies contract-001 clarification on header format — frontend countdown logic depends on this.
