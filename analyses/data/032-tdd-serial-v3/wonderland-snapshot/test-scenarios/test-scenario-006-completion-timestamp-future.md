## Test Scenario 006: Completion timestamp in future — indicates clock skew, rejected

**Feature:** Focus session with visual countdown
**Axis:** Input validation
**Type:** Fragility / data sanity check
**Severity:** medium
**Related artifact:** contract-note-005-session-completion-event-and-backend-logging

### Scenario

Frontend sends completed_at timestamp in the future (e.g., due to client clock skew or data corruption). Backend rejects as invalid.

1. Frontend sends:
   ```json
   {
     "type": "focus",
     "duration_configured_seconds": 1500,
     "duration_actual_seconds": 1500,
     "completed_at": "2024-01-15T15:30:00+00:00"  // Now is 14:30; this is 1 hour in future
   }
   ```
2. Backend validates: completed_at > now() → invalid
3. Backend returns 4xx response
4. Frontend sees error, may retry or log alert

### Concern

Future timestamps should never occur in a session-completion log (a session cannot complete before its recording). Rejecting them prevents history from including nonsensical entries and may surface a client clock skew problem that should be investigated.

### Test File

`tests/test_focus_session_with_visual_countdown.py::test_focus_session_completion_timestamp_in_future`
