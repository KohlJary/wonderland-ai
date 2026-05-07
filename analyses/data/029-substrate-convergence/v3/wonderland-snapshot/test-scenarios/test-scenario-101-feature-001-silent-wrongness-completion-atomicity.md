# Test Scenario 101: Feature 001 — Silent Wrongness: Completion Atomicity

**Feature:** Run a focused work session with built-in break
**Severity:** silent-wrongness
**Concern:** State machine transitions are easy to miss—the implementation will count down correctly but forget to emit the completion event or will fire the event but not atomically write the SessionRecord. Marcus stares at a timer stuck at 00:00. No notification fires. Later, when he force-quits or manually ends the session, the data is lost from history—or worse, partial writes leave the session in a zombie state. This is the most dangerous failure mode: the system appears to work (countdown happens) but produces silently wrong output (no state transition, no history record).

## Scenario

Marcus has started a session. The countdown is running. System clock is synchronized. No other sessions are running.

The countdown reaches 00:00—the full 25-minute duration has elapsed.

## Expected

The timer immediately transitions to 'break' state. The UI shows 'Break: 5:00' and begins counting down. A SessionRecord is written to history with the session timestamp and actual duration.

## Failure Mode

Session completion fires but the state machine transition doesn't occur, OR the transition fires but the SessionRecord write doesn't. Partial writes are not allowed. This is silent-wrongness because Marcus sees the countdown stop (looks OK) but the system is internally inconsistent: no notification, no history, no break timer.

## Property

For all sessions S that complete (elapsed_time >= session_length), within 500ms of completion: S.status transitions to 'break' (or 'completed' if no break follows) AND an immutable SessionRecord is atomically written with the actual session_duration_ms calculated as (elapsed_ms - paused_duration_ms). Both transitions succeed or both roll back; partial writes do not occur.

## Test Implementation

See `tests/test_feature_001_completion_atomicity.py` for runnable tests.

## Implies

- Depends on backend state machine atomicity—Tweedles own the implementation.
- Implies notification mechanism contract—Alice flagged this as a confusion-flag; need to settle whether it's frontend notification API or backend signal.
