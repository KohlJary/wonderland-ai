## Scenario 013: Break timer pause and resume preserves remaining time

**Severity:** degradation

**Setup:**

Break timer is running with 300 seconds remaining (out of 600 total).

**Trigger:**

Keisha taps pause. The countdown should freeze. After 30 seconds of real time, she taps resume. The timer should still show 300 seconds remaining (the pause point), not 270.

**Expected:**

Break session status='running', remaining_seconds=300 (unchanged during pause window). After resume, remaining_seconds still <=300 (not 270).

**Concern:**

If pause doesn't freeze elapsed time, the countdown continues to advance even though the UI shows 'paused.' After resume, the timer jumps backward or forward, confusing the user.

**Property:**

If a session is paused at time T with remaining_seconds = R, and the wall-clock time advances by N seconds while the session stays paused, then remaining_seconds should still equal R when retrieved (or R + small_drift, depending on implementation).

**Implies:**
- Backend-side: pause action must record the pause time and not advance elapsed time while paused.
- Frontend-side: display remaining_seconds as frozen while paused.
