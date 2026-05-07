## Test Scenario: Concurrent session start requests from same user

**Severity:** high

**Feature:** Feature-001 (Start and complete a focus session with breaks)

**Setup:**

User's frontend sends two `/sessions/start` requests within 100ms of each other (e.g., button double-click, or two tabs of the same app).

Request 1:
```json
{ "session_type": "focus", "focus_duration_seconds": 1500, "break_duration_seconds": 300 }
```

Request 2: (identical, sent nearly simultaneously)
```json
{ "session_type": "focus", "focus_duration_seconds": 1500, "break_duration_seconds": 300 }
```

**Trigger:**

Both requests reach the backend before either completes.

**Expected:**

- First request: 200 OK, returns session_id="abc-123"
- Second request: either
  - 409 Conflict (cannot start a new session when one is already active), or
  - 200 OK with session_id="def-456" (new session created, but backend has enforced only one active session per user at a time)

Result: Only one session is marked "active" at any time. Subsequent completion events reference only one session_id.

**Concern:**

Without concurrency controls, a user can accidentally create multiple overlapping "active" sessions. This can lead to:
- Nonsensical session counts (user thinks they completed 1 session but 2 are recorded)
- Ambiguous state during phase transitions (which session's timer is running?)
- Incorrect elapsed-time calculations if sessions overlap

**Property:**

At any moment, a given user has at most one "active" (non-completed) session. Starting a new session while one is active either rejects the new start with 409 Conflict, or automatically completes the prior session.

**Mechanism:**

Backend tracks an `active_session_id` per user. Before accepting a new start, check if one already exists. If yes, either reject (409) or auto-complete the prior one and allow the new one.

**Runnable Tests:**

- `tests/test_feature_001_edge_cases.py::test_feature_001_concurrent_start_requests_from_same_user`
