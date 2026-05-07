## Scenario 008: Rate limit enforcement is atomic; no race condition where two concurrent requests at quota both pass

**Severity:** breakage

**Setup:**

Quota is exactly 1 request per 60-second window. Client is at 0 requests in current bucket. Two concurrent POST /api/messages requests arrive from same client in same millisecond.

**Trigger:**

Two requests are processed concurrently (thread pool or event loop interleaving).

**Expected:**

First request returns 200 (quota goes 0→1). Second request returns 429 (1 >= 1 quota exhausted). OR both are rejected (conservative). Bucket state remains consistent; exactly one request succeeds.

**Concern:**

If rate limiter has race condition (check-then-increment, not atomic), both requests might see count=0 and both return 200. Silent wrongness: two messages arrive when quota is 1. Downstream: duplicate processing, inconsistent state visible to users.

**Property:**

For all quota values Q and concurrent requests at request_count=0, at most Q requests succeed in the window. Success count is deterministic (not thread-schedule-dependent).

**Implies:**
- Implies backend must use atomic operations (Redis atomic increment or database transaction), not in-memory accumulator.
