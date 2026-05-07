# Test Scenario 002: Pause and resume accumulate pause time correctly

**Severity:** breakage

**Setup:**

Casey is in the middle of a 25-minute focus session. The countdown shows `18:45` (6 minutes and 15 seconds have elapsed). The session is currently `status=running`. Casey is interrupted by a phone call.

**Trigger:**

Casey clicks the Pause button on the session timer UI.

**Expected:**

1. The countdown stops incrementing (stays at `18:45`).
2. The session `status` changes to `paused`.
3. The UI shows Pause is complete and offers Resume / Abandon buttons.
4. The `paused_duration_ms` in the Session record is set to approximately 0 (the pause just happened).

After 3 minutes, Casey finishes the call and clicks Resume:

5. The session `status` changes back to `running`.
6. The countdown continues from `18:45` (not reset to `25:00`).
7. The `paused_duration_ms` in the Session record increases by approximately 3 minutes (the pause time).

If Casey is interrupted again and pauses a second time after 2 more minutes of work:

8. The countdown pauses at approximately `16:45` (18:45 - 2 min).
9. The second pause occurs, and `paused_duration_ms` increases by another 2 minutes (total now ~5 minutes).

**Concern:**

Pause/resume is easy to get wrong:
- The `paused_duration_ms` field might not accumulate; instead, it might be reset on each pause (so total pause time is lost).
- The elapsed time might not be tracked correctly across pause/resume cycles, causing the final session duration to be wrong.
- The countdown might jump backward or forward incorrectly after resume.
- The frontend might not reconcile its local timer with the backend's paused_duration on resume, causing the timer display to be out of sync.
- Multiple pause/resume cycles might cause the pause duration to be counted twice or not at all.

**Property:**

For all sessions S with N pause/resume cycles, where pause_i occurs at elapsed_i and resumes after duration_i:
- The `paused_duration_ms` after all cycles = sum(duration_1, duration_2, ..., duration_N).
- The final session_duration (elapsed - paused_duration) reflects only the actual work time, not the pauses.
- The displayed countdown at each step is consistent with (session_length - elapsed + paused_duration).

**Implies:**

- Implies backend accumulation of paused_duration_ms across multiple pause/resume cycles — flag for Tweedledum.
- Implies frontend reconciliation with paused_duration on every status update — flag for Tweedledee.
