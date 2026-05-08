## Test Scenario 007: Invalid duration type — non-numeric duration rejected

**Feature:** Focus session with visual countdown
**Axis:** Input validation
**Type:** Fragility / type safety
**Severity:** high
**Related artifact:** contract-note-005-session-completion-event-and-backend-logging

### Scenario

Frontend sends duration as a non-numeric type (e.g., string). Backend type validation rejects.

1. Frontend sends:
   ```json
   {
     "type": "focus",
     "duration_configured_seconds": 1500,
     "duration_actual_seconds": "not a number",  // String instead of int
     "completed_at": "2024-01-15T14:30:00+00:00"
   }
   ```
2. Backend validation fails (4xx response, likely 422 Unprocessable Entity)
3. Error is reported to frontend

### Concern

If backend accepts non-numeric durations, downstream logic (history aggregation, statistics) will fail or produce garbage. Type validation at the boundary ensures all recorded sessions have numeric, comparable duration values.

### Test File

`tests/test_focus_session_with_visual_countdown.py::test_focus_session_invalid_duration_type`
