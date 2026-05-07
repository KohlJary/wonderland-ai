## Scenario 005: Marcus starts a session, then immediately toggles between 'app in foreground' and 'app in background' (switches away and back rapidly)

**Severity:** curiosity

**Setup:**

Marcus taps Start. The timer is at 24:59. He immediately switches to another app (app goes to background). The timer was mid-tick.

**Trigger:**

App background, then foreground, then background again — three times in rapid succession, over 2 seconds total.

**Expected:**

The timer continues accurately. The total elapsed time on the session is correct when he returns.

**Concern:**

Depending on the pause/resume implementation, the app might not handle rapid app state changes smoothly. Timers might not pause correctly, or the pause/resume logic might have a race condition that causes the elapsed time to drift.

**Property:**

For all sessions in 'background' state, the timer logic is paused (time does not advance). On return to foreground, elapsed time resumes from where it was paused, not from current system time.
