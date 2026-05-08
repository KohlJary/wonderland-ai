## Scenario: Two clients attempt to log the same session completion simultaneously

**Severity:** data-corruption

**Setup:**

A user is operating two browser tabs concurrently. Tab A completes a focus session at approximately the same time as Tab B attempts to complete the same session. Both clients generate completion events for the same session_id and submit them to the backend within milliseconds of each other.

**Trigger:**

Two POST requests arrive at the backend:
```
Request A: POST /api/sessions/session-123/complete
           {"type": "focus", "duration_ms": 1500000}

Request B: POST /api/sessions/session-123/complete
           {"type": "focus", "duration_ms": 1500000}
```

Both requests reference the same session_id and have identical payloads. They may be processed concurrently at the database level (race condition).

**Expected:**

The event log contains exactly ONE entry for session_id session-123, not two. Both POST requests should succeed (200 or 201), with the second one being idempotent. Daily review must count the session exactly once, with total_focus_time_ms equal to 1500000, not double-counted.

**Concern:**

If the backend does not prevent duplicate entries for the same session_id, the race condition will result in two rows in the event log. When daily review aggregates, it will SUM the durations (3000000 instead of 1500000) and COUNT twice (wrong). This is data corruption: the user's daily stats will be silently incorrect. They will think they completed 2 sessions when they completed 1. This is difficult to detect because the UI will just display the inflated numbers without error flags.

The contract note for feature 003 states the invariant: "each session_id appears exactly once in the log". This invariant must be enforced at the database level (UNIQUE constraint on session_id in the event_log table) to prevent race conditions, not just at the application level (where it can fail under concurrent load).

**Property:**

For all concurrent pairs of completion requests R1, R2 for the same session_id S:
- After both R1 and R2 complete, count(event_log entries with session_id = S) == 1
- The daily review for the session's date must report the correct counts (not duplicated)

**Implies:**

- Implies schema: event_log table must have a UNIQUE constraint on (session_id)
- Implies idempotency: the second request for the same session_id must not increment counts; it should return 200 OK (idempotent) or 409 Conflict (rejected duplicate)
- Implies atomicity: the INSERT operation must be atomic with the uniqueness check; no gap where both reads succeed and both writes proceed
- Implies testing: test suite must verify that concurrent requests to the same endpoint result in single-entry state, not doubled

**Test Coverage:**

`tests/test_daily_review_fragility.py::TestConcurrentSessionLogging::test_concurrent_completion_requests_for_same_session_result_in_single_log`
