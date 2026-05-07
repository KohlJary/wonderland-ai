## Scenario 011: Frontend respects Retry-After; no manual retry before countdown expires

**Severity:** degradation

**Setup:**

User is rate-limited on POST /api/messages (429 with Retry-After: 30). User tries to submit another message before 30 seconds have passed.

**Trigger:**

User clicks 'Submit' button while countdown timer is ticking down.

**Expected:**

Frontend checks retry_available_at and finds it is in future. Request is NOT sent to backend. UI renders error or queues locally. Countdown timer visible. After timer reaches zero, request proceeds.

**Concern:**

If frontend doesn't respect Retry-After and sends request anyway, backend rejects with another 429. User sees repeated error messages (poor UX). Multiple requests during rate-limit window waste recovery time and may lock user out further. Contract-005 specifies 'user cannot manually retry until countdown reaches zero.' This is UX requirement with backend contract implications.

**Property:**

For all 429 responses with Retry-After = R, frontend does not send next request until wall-clock time >= response_time + R.

**Implies:**
- Implies contract-005: frontend countdown must be based on Retry-After header; manual retry is blocked until expiry.
