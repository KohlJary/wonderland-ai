## Test Scenario: Transition from focus to break phase preserves session_id and state consistency

**Severity:** silent-wrongness

**Feature:** Feature 001: Run a focus session with breaks

**Setup:**

User has started a session with session_id=abc-123. Frontend sent POST /sessions/start {session_id, focus_minutes: 25, break_minutes: 5}. Backend created current_session in focus phase.

**Trigger:**

Timer fires at 25 minutes, backend attempts phase transition to break.

**Expected:**

current_session.phase changes from 'focus' to 'break'. current_session.elapsed_time resets to 0 (for break countdown). current_session.state remains 'running'. Session_id is invariant across transition. No data loss.

**Concern:**

State machine edge case: if the phase transition logic doesn't reset elapsed_time for the new phase, frontend interprets elapsed_time=1500 as 'break timer already 25 minutes through'—user sees break timer appear and immediately expire. Or if session_id is lost during transition (overwrite instead of update), backend loses track of which user's session this is.

**Property:**

For all session transitions T from phase P1 to phase P2, session_id is invariant and elapsed_time for P2 starts at 0.

**Implications:**

None noted.
