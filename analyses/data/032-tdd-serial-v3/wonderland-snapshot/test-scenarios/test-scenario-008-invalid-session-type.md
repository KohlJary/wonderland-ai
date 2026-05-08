## Test Scenario 008: Invalid session type — unknown type rejected

**Feature:** Focus session with visual countdown
**Axis:** Input validation
**Type:** Fragility / enum constraint
**Severity:** high
**Related artifact:** contract-note-005-session-completion-event-and-backend-logging

### Scenario

Frontend sends a session type that is not one of the allowed enum values ('focus' or 'break'). Backend validation rejects.

1. Frontend sends:
   ```json
   {
     "type": "meditation",  // Not in allowed enum
     "duration_configured_seconds": 1500,
     "duration_actual_seconds": 1500,
     "completed_at": "2024-01-15T14:30:00+00:00"
   }
   ```
2. Backend validation fails (4xx response)
3. Error is reported to frontend

### Concern

If backend accepts arbitrary session types, downstream history queries and aggregations (e.g., "total focus time") become ambiguous. Strict enum validation ensures history is consistent and interpretable.

### Test File

`tests/test_focus_session_with_visual_countdown.py::test_focus_session_invalid_session_type`
