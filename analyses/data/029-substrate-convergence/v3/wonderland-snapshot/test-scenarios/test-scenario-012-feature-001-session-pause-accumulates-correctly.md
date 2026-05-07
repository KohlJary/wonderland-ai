## Test Scenario 012: Pause duration accumulates correctly across multiple pauses

**Severity:** silent-wrongness

**Feature:** Feature 001: Run a focused work session with built-in break

**Setup:**

Marcus is 10 minutes into a 25-minute session. The timer shows 15:00 remaining. He pauses the session to take a phone call.

**Trigger:**

Marcus taps the Pause button. 30 seconds later, he resumes. Then, 5 minutes into the resumed countdown, he pauses again for 45 seconds, then resumes again. The session continues until completion.

**Expected:**

The final SessionRecord should record:
- session_duration_ms = actual focused time (excluding both pause periods) ≈ (10 + 5 + remaining) × 60 × 1000
- paused_duration_ms = 30 + 45 = 75 seconds

When Marcus reviews his session in history, it shows the correct focused duration (pauses not counted against focus time).

**Concern:**

If pause-duration accumulation is not handled atomically, or if the backend resets paused_duration_ms on resume instead of accumulating it, the final SessionRecord will show incorrect session_duration_ms. The user will think they focused longer than they actually did, corrupting their daily/weekly aggregates.

Additionally, if the frontend doesn't reconcile paused_duration_ms on every status update from the backend, the local timer display will drift from the server's truth.

**Property:**

For all sessions with N pauses, final_session_duration_ms = (total_wall_clock_time - sum_of_all_pause_durations) × 1000. Pause duration is monotonically increasing, never resets mid-session, and is always >= previous pause duration.

**Implies:**

Implications: This tests the atomic transaction contract for pause/resume state. Also tests the history query's accuracy (Feature 002 depends on correct session_duration_ms).

