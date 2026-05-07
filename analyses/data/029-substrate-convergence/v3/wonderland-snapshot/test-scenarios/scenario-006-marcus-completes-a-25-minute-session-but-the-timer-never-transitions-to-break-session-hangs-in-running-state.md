## Scenario 006: Marcus completes a 25-minute session but the timer never transitions to break—session hangs in 'running' state

**Severity:** silent-wrongness

**Setup:**

Marcus has started a session. The countdown is running. System clock is synchronized. No other sessions are running.

**Trigger:**

The countdown reaches 00:00—the full 25-minute duration has elapsed.

**Expected:**

The timer immediately transitions to 'break' state. The UI shows 'Break: 5:00' and begins counting down. A SessionRecord is written to history with the session timestamp and actual duration.

**Concern:**

The implementation will count down correctly but forget to emit the completion event or will fire the event but not atomically write the SessionRecord. Marcus stares at a timer stuck at 00:00. No notification fires. Later, when he force-quits or manually ends the session, the data is lost from history—or worse, partial writes leave the session in a zombie state (marked incomplete in the session table but recorded in history, or vice versa). This is the most dangerous failure mode: the system appears to work (countdown happens) but produces silently wrong output (no state transition, no history record).

**Property:**

For all sessions S that complete (elapsed_time >= session_length), within 500ms of completion: S.status transitions to 'break' (or 'completed' if no break follows) AND an immutable SessionRecord is atomically written with the actual session_duration_ms calculated as (elapsed_ms - paused_duration_ms). Both transitions succeed or both roll back; partial writes do not occur.

**Implies:**
- Depends on backend state machine atomicity—Tweedles own the implementation.
- Implies notification mechanism contract—Alice flagged this as a confusion-flag; need to settle whether it's frontend notification API or backend signal.
