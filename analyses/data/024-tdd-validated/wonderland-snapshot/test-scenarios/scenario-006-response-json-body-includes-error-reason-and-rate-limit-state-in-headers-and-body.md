## Scenario 006: Response JSON body includes error reason and rate-limit state in headers and body

**Severity:** degradation

**Setup:**

Client exceeds quota on POST /api/messages. Backend returns 429.

**Trigger:**

Frontend parses response body.

**Expected:**

429 response body is valid JSON with: (1) error reason field ('error': 'rate_limit_exceeded' or similar), (2) numeric fields matching header values: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset (for convenience in parsing).

**Concern:**

If response body is absent (only headers), frontend must parse headers. If body includes only status without reason, frontend can't distinguish from other 4xx errors. If body fields don't match header values, silent inconsistency occurs (frontend shows one number, logs show another). Contract-001 asks what the JSON shape is; contract-005 expects frontend to display user-friendly error.

**Property:**

For all 429 responses, JSON body includes a distinct 'reason' or 'error' field explicitly identifying the error as rate-limit (not auth, not validation).

**Implies:**
- Implies contract-001 must specify exact JSON shape before frontend can ship reliable error handling.
