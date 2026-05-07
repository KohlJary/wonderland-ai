## Scenario 007: X-RateLimit-Reset is absolute wall-clock timestamp, not relative; frontend countdown works across clock skew

**Severity:** silent-wrongness

**Setup:**

Rate limiter uses 60-second bucket window. Client exhausts quota at T=00:00:00. Response includes X-RateLimit-Reset header (absolute timestamp). Frontend stores retry_available_at = X-RateLimit-Reset value.

**Trigger:**

Frontend's local clock drifts backward 5 seconds. Frontend checks retry_available_at again at T=00:00:55.

**Expected:**

retry_available_at is still X-RateLimit-Reset value (stored on first 429). Frontend countdown shows 5 seconds remaining. At T=00:01:00, frontend sends next request and is allowed.

**Concern:**

If frontend uses Retry-After as relative delay (sleep 60 seconds from first 429), clock skew causes requests to fire too early or too late (silent wrongness). If X-RateLimit-Reset is ambiguous (seconds-since-epoch vs. milliseconds), frontend countdown fails. Contract-003 must specify X-RateLimit-Reset format (unix seconds? milliseconds? which epoch?).

**Property:**

For all 429 responses with X-RateLimit-Reset = T_reset, requests queued for retry before T_reset are held; requests at or after T_reset are allowed.

**Implies:**
- Implies contract-003: X-RateLimit-Reset must specify format explicitly. Frontend countdown logic depends on this.
