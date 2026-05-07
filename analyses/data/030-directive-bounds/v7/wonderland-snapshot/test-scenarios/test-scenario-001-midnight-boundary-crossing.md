## Test Scenario: Session started before midnight, completed after midnight

**Severity:** silent-wrongness

**Feature:** Feature-001 (Start and complete a focus session with breaks)

**Setup:**

User's local clock is set to 11:58pm UTC. User starts a 25-minute focus session. The frontend calculates `started_at` as an ISO8601 timestamp (2024-01-15T23:58:00Z).

**Trigger:**

Session runs for 25 minutes of elapsed time. Midnight passes during the session (at 00:00:00 UTC on Jan 16). The frontend completes the session and generates a completion event with `completed_at = 2024-01-16T00:23:00Z`.

**Expected:**

Backend receives the completion event and records both `started_at` and `completed_at` with their full calendar dates intact. The session's `focus_duration_seconds` is recorded as 1500 (25 minutes), not truncated or wrapped. When the user queries history, the session appears in the correct date window and the duration is accurate.

**Concern:**

Frontend may miscalculate timestamps when the calendar day boundary is crossed mid-session. The date components of the timestamps might be corrupted (e.g., both marked as Jan 16, losing the start date). Silent wrongness: the session was completed, the event was posted, but the recorded timestamps are wrong and this is invisible until the user exports or carefully examines a history query that shows contradictory dates.

**Property:**

For all sessions where `started_at.date() != completed_at.date()` (crossing midnight), the `focus_duration_seconds` must equal the wall-clock time delta, and both date components of the timestamps must be preserved exactly as sent.

**Implies:**

- Feature-002 (history queries) must correctly handle sessions spanning calendar boundaries. If Feature-002 shows "today = last 24 hours from now" and a session started at 11:58pm yesterday and ended at 12:23am today, the query must consistently include or exclude the session without duplication. Implies a contract clarification for Tweedles on window-boundary behavior.

**Runnable Tests:**

- `tests/test_sessions_core_failures.py::TestMidnightBoundaryCrossing::test_session_completion_event_preserves_wall_clock_time_across_midnight`
- `tests/test_sessions_core_failures.py::TestMidnightBoundaryCrossing::test_session_history_query_counts_midnight_spanning_session_in_correct_windows`
