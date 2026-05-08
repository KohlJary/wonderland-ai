## Test Scenario 002: Timer drift — actual time exceeds configured by up to 5%

**Feature:** Focus session with visual countdown
**Axis:** Session completion and timer accuracy
**Type:** Fragility / edge case
**Severity:** high
**Related artifact:** contract-note-005-session-completion-event-and-backend-logging

### Scenario

Due to system load, GC pauses, or scheduler latency, the actual elapsed time exceeds the configured duration, but within the 5% tolerance window.

1. User starts focus session (configured 25 minutes = 1500 seconds)
2. System experiences latency (GC pause, CPU contention, etc.)
3. Timer reports completion at 1537 seconds (actual = 1500 + 37 = 102.5% of configured, within 5% tolerance)
4. Frontend POSTs:
   ```json
   {
     "type": "focus",
     "duration_configured_seconds": 1500,
     "duration_actual_seconds": 1537,
     "completed_at": "2024-01-15T14:30:37+00:00"
   }
   ```
5. Backend accepts the request (200 OK) because actual ≤ configured + 5%
6. Session is logged

### Concern

If backend rejects valid timer drift within the 5% window, legitimate sessions (especially those run on busy systems) will fail to log. If backend accepts arbitrarily large drift, it loses ability to detect timer bugs or data corruption.

The 5% threshold is the contract boundary: it's realistic variance; beyond it indicates a problem.

### Test File

`tests/test_focus_session_with_visual_countdown.py::test_focus_session_timer_drift_within_tolerance`
