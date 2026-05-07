# Test Scenario 001: Session timer countdown accuracy and completion notification

**Severity:** breakage

**Setup:**

Maya is using the pomodoro app on her laptop. She has opened the app fresh. The default Settings are in place (25-minute session, 5-minute break). She has not started any sessions yet. Her local system time is accurate.

**Trigger:**

Maya clicks the "Start Session" button on the main screen.

**Expected:**

1. The app displays a countdown timer showing `25:00`.
2. The countdown visibly decrements every second: `24:59`, `24:58`, ... `00:01`, `00:00`.
3. The countdown is accurate to within 1 second of the actual elapsed time (accounting for browser/app latency, not frontend local clock drift).
4. When the countdown reaches `00:00`, the app produces a notification (visual, audio, or both) that is clearly visible/audible to Maya.
5. The Session record transitions to `status=completed` in the database.
6. A SessionRecord is written to the database with:
   - `completed_at` = the time the countdown reached zero
   - `session_duration_ms` ≈ 25 minutes (within ±1 second)
   - `session_type` = 'focus'
7. The app transitions to a break countdown state, showing `05:00` and counting down.

**Concern:**

This is the core feature. If the timer doesn't work:
- Maya loses trust in the app to track time (she'll watch the clock instead of the timer).
- The notification might fail silently (app in background, notification settings off).
- The Session might not persist to the database, so history is incomplete.
- The state machine might hang (countdown completes but status never changes, break never starts).
- Frontend timer might drift ahead or behind due to device clock being wrong, showing Maya incorrect remaining time.

**Property:**

For all sessions S with session_length_minutes=L, starting at time T_start:
- The countdown displayed is approximately (L*60 - elapsed_seconds) at time T_start + elapsed_seconds.
- When elapsed_seconds ≥ L*60, a completion notification is emitted and Session.status=completed.
- A SessionRecord is written atomically with completed_at, session_duration_ms, and session_type.
- Clock drift between frontend and backend does not cause a countdown that either completes instantly or runs indefinitely.

**Implies:**

- Implies frontend timer reconciliation on every Session.status update — flag for Tweedledee.
- Implies backend Session state machine enforcement — flag for Tweedledum.
- Implies atomic SessionRecord write on completion — flag for Tweedledum.
- Implies notification system (either in-browser notification API or app native) — flag for Tweedledee.
