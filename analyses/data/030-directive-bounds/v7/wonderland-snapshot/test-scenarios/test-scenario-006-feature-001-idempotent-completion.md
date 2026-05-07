## Test Scenario: Duplicate session completion events must be idempotent

**Severity:** high

**Feature:** Feature-001 (Start and complete a focus session with breaks)

**Setup:**

User completes a 25-minute focus session. Frontend POSTs to `/sessions/complete` with:
```json
{
  "session_id": "abc-123",
  "session_type": "focus",
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:25:00Z",
  "focus_duration_seconds": 1500,
  "break_duration_seconds": 300
}
```

**Trigger:**

Network glitch causes the request to be retried. Frontend re-sends the identical payload.

**Expected:**

Both requests return 200 OK with the same session_id. The session is recorded exactly once in the backend database. When user queries GET /sessions?window=today, the session count is 1, not 2.

**Concern:**

Without idempotency guarantees, retryable network failures can corrupt the session count. This is the most common failure mode in distributed systems: a client retries a failed POST, intending to fix an outage, but if the first request actually succeeded (network error on the response), the second request creates a duplicate. The user then sees false-doubled session counts and loses trust in the tracking system.

**Property:**

For any session completion POST with identical (session_id, completed_at) pair, the backend must be idempotent: second and subsequent POSTs must return 200 OK (not 409 Conflict) and must not create duplicate session records.

**Mechanism:**

Backend enforces a unique constraint on (session_id, completed_at) or uses (user_id, session_id, completed_at) as the primary key. Retried POSTs with the same key are recognized as duplicates and return the existing record.

**Runnable Tests:**

- `tests/test_feature_001_edge_cases.py::test_feature_001_duplicate_completion_idempotency`
