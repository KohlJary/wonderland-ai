## Scenario: Session is completed twice (double-post of completion event)

**Severity:** silent-wrongness

**Setup:**

User completes a focus session. The frontend issues a POST to log the completion. The backend receives it, logs it, and sends 200. But the frontend doesn't receive the response (network flake, timeout). Frontend retries. Backend receives the same session_id again.

**Trigger:**

Backend receives two POST requests with:
```json
{"session_id": "abc123", "type": "focus", "duration_ms": 1500000, "status": "completed"}
```

The two requests are identical and arrive within seconds of each other.

**Expected:**

The event log contains exactly ONE entry for session "abc123", not two. Daily review counts 1 completed session, not 2.

**Concern:**

Without idempotency, the daily stats will be wrong. The same session will be counted twice, doubling the daily focus time and session count. This is silent wrongness because the UI will just display the inflated numbers without error. The aggregation query will sum both rows.

The contract note says "Invariant: each session_id appears exactly once in the log" but doesn't specify the mechanism: is it a UNIQUE constraint on session_id in the DB? Is it a deduplication on the backend that rejects the duplicate before inserting? Is there a timestamp check ("if a session_id with the same type was logged in the last 5 seconds, ignore")?

**Property:**

For all sessions S and completion events E1, E2 with E1.session_id == E2.session_id and E1 == E2:
- After both E1 and E2 are submitted to the log, count(log entries for S.session_id) == 1

**Implies:**

- Implies backend schema: event log table must have a UNIQUE constraint on (session_id) OR deduplication logic in the endpoint
- Implies contract clarification: what is the deduplication strategy? DB constraint? Endpoint logic? Idempotency token?
- Implies test structure: happy-path test for idempotent completion logging
