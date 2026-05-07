## Scenario 004: Marcus is in a session when his system clock jumps backward (NTP correction, user manually adjusts clock)

**Severity:** degradation

**Setup:**

Marcus has been in a session for 10 minutes. System time is 14:32:15. The timer shows 15:10 remaining.

**Trigger:**

System clock jumps backward to 14:20:00 (a 12-minute rewind).

**Expected:**

The timer continues counting down from approximately 15:10. The session still completes at the correct wall-clock duration (25 minutes from start_time), not from system.now().

**Concern:**

The implementation uses system.now() directly in the countdown loop instead of calculating elapsed_time as (system.now() - session.started_at). When the clock jumps backward, the remaining time calculation becomes wrong. The timer may show negative time, freeze, or skip forward.

**Property:**

For all sessions S, the remaining time at any point is max(0, S.duration - (system.now() - S.started_at)). Clock adjustments do not cause remaining_time to go negative or jump discontinuously.

**Implies:**
- Implementation detail for Tweedles — use elapsed time, not absolute time.
