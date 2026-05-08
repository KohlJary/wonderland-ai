## Test Scenario 003: Timer drift — actual time exceeds configured by more than 5%

**Feature:** Focus session with visual countdown
**Axis:** Session completion and data validation
**Type:** Fragility / validation boundary
**Severity:** high
**Related artifact:** contract-note-005-session-completion-event-and-backend-logging

### Scenario

The actual elapsed time exceeds the configured duration by more than 5%, indicating a timer malfunction or data corruption. Backend rejects the request.

1. User starts focus session (configured 25 minutes = 1500 seconds)
2. Due to a timer bug or extreme system load, timer reports completion at 1600 seconds (actual = 106.7% of configured, EXCEEDS 5% tolerance)
3. Frontend POSTs:
   ```json
   {
     "type": "focus",
     "duration_configured_seconds": 1500,
     "duration_actual_seconds": 1600,
     "completed_at": "2024-01-15T14:30:40+00:00"
   }
   ```
4. Backend validation rejects (4xx response)
5. Frontend sees error, may retry or log local alert

### Concern

Data integrity: accepting timers that run 6%+ over configured duration would pollute history with unreliable measurements. Rejecting beyond 5% protects against both timer bugs and data corruption. The boundary must be enforced.

### Test File

`tests/test_focus_session_with_visual_countdown.py::test_focus_session_timer_drift_exceeds_tolerance`
