## Test Scenario 015: Device clock set ahead does not break timer or show negative time

**Severity:** silent-wrongness

**Feature:** Feature 001: Run a focused work session with built-in break

**Setup:**

Marcus starts a 25-minute session at server time T=12:00 PM. The backend records started_at=12:00:00 UTC. Marcus's phone's local clock is set 2 hours ahead (due to a clock sync bug, user error, or test simulation). From his phone's perspective, the current time is 2:00 PM.

**Trigger:**

Marcus looks at the timer on his phone. The frontend calculates:
  remaining_ms = (started_at + session_duration) - local_now
  remaining_ms = (12:00 + 25 min) - 14:00 = 12:25 - 14:00 = negative!

If the frontend doesn't handle this, it might display "-95 minutes remaining" or "00:00 (already expired)" even though only a few seconds have actually passed.

**Expected:**

The frontend should never display negative time remaining. Instead, it should:
1. Detect that local_now is significantly ahead of server_started_at + elapsed.
2. Request the current session status from the backend.
3. Reconcile with the server's truth: the session is still running, time remaining is 24:50 (or similar).
4. Reset the local timer to the correct elapsed time based on server_started_at.

The countdown continues normally from this point. The timer does not appear "expired" or show negative time.

**Concern:**

If the frontend trusts the device's local clock without reconciliation, users with misconfigured device clocks will see confusing behavior: sessions appearing to be already complete, countdowns jumping backward, or timer appearing frozen. This is a silent wrongness because the user might think the app is broken, even though the app is correctly reflecting a broken device clock.

**Property:**

For all sessions, displayed_time_remaining >= 0 always. If local_clock - server_started_at exceeds the expected elapsed time by more than 1 second, the frontend must reconcile with the backend.

**Implies:**

This tests the frontend's clock drift detection and reconciliation logic. The contract specifies "clock drift >1s triggers hard reset." This scenario validates the implementation.

