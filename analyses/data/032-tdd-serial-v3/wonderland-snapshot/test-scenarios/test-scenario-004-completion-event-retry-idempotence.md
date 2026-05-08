## Test Scenario 004: Completion event retry — duplicate POST from network retry is idempotent

**Feature:** Focus session with visual countdown
**Axis:** Network resilience and duplicate handling
**Type:** Fragility / retry semantics
**Severity:** critical
**Related artifact:** contract-note-005-session-completion-event-and-backend-logging

### Scenario

Network fails on the first POST; frontend retries. Backend must detect the duplicate and return the same session_id without creating a second session record.

1. User completes focus session
2. Frontend POSTs session completion
3. Network error (timeout, 5xx, etc.) occurs
4. Frontend waits 1s + exponential backoff, retries
5. Second POST succeeds
6. Backend recognizes the duplicate (same completed_at timestamp) and returns the original session_id
7. Single session record exists; no duplicates

Example flow:
- First POST: { type: "focus", ..., completed_at: "2024-01-15T14:30:00+00:00" } → fails
- Second POST: { type: "focus", ..., completed_at: "2024-01-15T14:30:00+00:00" } → succeeds, returns same session_id

### Concern

Without idempotence, retries create duplicate session records, polluting history with false counts (e.g., "user completed 5 sessions" when they completed 3). Idempotence must be keyed on (user_id, completed_at, type) or a deterministic identifier derived from them.

### Test File

`tests/test_focus_session_with_visual_countdown.py::test_focus_session_completion_event_retry_succeeds`
