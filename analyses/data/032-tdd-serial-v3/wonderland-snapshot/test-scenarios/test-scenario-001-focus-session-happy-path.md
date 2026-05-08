## Test Scenario 001: Focus session happy path — completion logs successfully

**Feature:** Focus session with visual countdown
**Axis:** Session completion and backend logging
**Type:** Happy path / core flow
**Severity:** critical
**Related artifact:** contract-note-005-session-completion-event-and-backend-logging

### Scenario

User completes a 25-minute focus session from start to finish with no network issues.

1. User opens app
2. User taps "Start Focus" (default 25 minutes)
3. Timer counts down visibly
4. Timer reaches 0:00
5. Frontend POSTs session completion to backend:
   ```json
   {
     "type": "focus",
     "duration_configured_seconds": 1500,
     "duration_actual_seconds": 1500,
     "completed_at": "2024-01-15T14:30:00+00:00"
   }
   ```
6. Backend responds with:
   ```json
   {
     "session_id": "abc123...",
     "acknowledged": true
   }
   ```
7. Session appears in daily history

### Concern

This is the load-bearing path: if session completion logging fails, the user's work is not recorded, and the daily review feature breaks downstream. Every completion must reach the backend successfully or retry until it does.

### Test File

`tests/test_focus_session_with_visual_countdown.py::test_focus_session_logs_completion_on_success`
