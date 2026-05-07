## Test Scenario: OS clock resets backward (NTP sync), session timer breaks

**Severity:** degradation

**Feature:** Feature-001 (Start and complete a focus session with breaks)

**Setup:**

User has a 25-minute focus session active. Session started at 12:00:00 UTC. Five minutes have elapsed (`elapsed_seconds = 300`). Frontend's `setInterval`-based countdown timer is running. At 12:05:30 UTC, the OS system clock jumps backward to 12:02:00 UTC due to an NTP time correction.

**Trigger:**

Frontend's timer logic depends on calculating remaining time as `focus_duration_seconds - elapsed_wall_clock_time`. The next timer tick happens after the clock jump.

**Expected:**

Session continues as if the clock jump didn't happen. `elapsed_seconds` continues from 300 (not reset to 120 based on the new wall clock). `time_remaining_seconds` correctly reflects remaining time, accounting for actual elapsed time since session start, not wall-clock delta. The countdown shows positive, monotonic timer values.

**Concern:**

Frontend may calculate `time_remaining = focus_duration_seconds - (now() - started_at)`, which would show negative or very large remaining time if `now()` jumps backward. The countdown might go backward, show a negative timer, or jump from 10 minutes remaining to 20 minutes remaining. User experience degrades to confusion ("did my timer break?") or perceived reset ("why is there suddenly more time?").

**Property:**

For all sessions, `elapsed_seconds` must be monotonically non-decreasing regardless of OS clock jumps. `time_remaining_seconds` must always be in the range `[0, focus_duration_seconds]` and must never increase (only decrease or stay constant) during an active session.

**Implies:**

- Frontend needs a defensive timer implementation — likely using a reference point (`session_start_time` saved at session start) and elapsed milliseconds accumulated via the browser's high-resolution timer (`performance.now()` or similar), not OS system time deltas. This is a frontend architecture concern; flag for Tweedledee.

**Runnable Tests:**

- `tests/test_sessions_core_failures.py::TestClockJumpBackward::test_session_elapsed_time_monotonic_across_clock_jump` (frontend test, placeholder)
- `tests/test_sessions_core_failures.py::TestClockJumpBackward::test_session_completion_with_negative_elapsed_time_in_payload_is_rejected`
