## Test Scenario 005: Malformed completion timestamp — invalid ISO8601 format rejected

**Feature:** Focus session with visual countdown
**Axis:** Input validation
**Type:** Fragility / malformed input
**Severity:** high
**Related artifact:** contract-note-005-session-completion-event-and-backend-logging

### Scenario

Frontend sends completed_at in an invalid format (e.g., missing time component, wrong timezone notation). Backend validation rejects.

1. Frontend sends:
   ```json
   {
     "type": "focus",
     "duration_configured_seconds": 1500,
     "duration_actual_seconds": 1500,
     "completed_at": "2024-01-15"  // Missing time component
   }
   ```
2. Backend validation fails (4xx response)
3. Error is reported to frontend for retry/logging

Valid format: ISO8601 with time component, e.g., "2024-01-15T14:30:00+00:00"

### Concern

If backend accepts non-ISO8601 timestamps, history queries (which assume ISO8601 for timezone-aware comparisons) will produce incorrect results. Strict validation at the boundary protects the invariant that every completed_at is a valid, parseable timestamp.

### Test File

`tests/test_focus_session_with_visual_countdown.py::test_focus_session_malformed_completion_timestamp`
