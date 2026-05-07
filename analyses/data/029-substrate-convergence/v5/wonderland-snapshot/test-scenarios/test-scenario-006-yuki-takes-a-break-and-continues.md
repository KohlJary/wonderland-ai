## Test Scenario 006: Yuki takes a break and continues the rhythm (User Journey)

**Feature:** Take a break and return to focus (feature-002)
**Persona:** Yuki, 28, writer. Uses pomodoro to structure her day. After a session, she wants a clear signal to step away, and a timer so her break doesn't vanish into scrolling.
**Stack span:** frontend + backend
**Severity:** critical
**Concern:** User happiness — does the break flow feel automatic and natural to the user Yuki?

**User Journey:**

Yuki's first 25-minute session just ended. The app notified her with sound and a banner: "Session complete!" She dismissed the notification.

Now, instead of returning to an empty "Start Session" screen, the app automatically shows her a break timer: "5:00" and counting down. She doesn't need to tap anything; the break started automatically. A small label says "Break time" to make the purpose clear.

Yuki gets up from her desk, makes a cup of tea, and checks her phone. She opens the pomodoro app to see how much break time is left. The timer shows "3:22" remaining. She knows she has time to finish her tea and get back to work without the break slipping away.

When the timer hits 0:00, the app notifies her again: "Break complete! Ready for the next session?" A button says "Start Next Session" and a secondary option says "Take another break."

Yuki taps "Start Next Session." The timer resets to 25:00 and starts counting down again. She's ready for her second session.

After five sessions, Yuki wants to take a longer break. On the 5th session completion, instead of auto-starting a break, she taps "Skip break" and then chooses "Custom break" → "10 minutes." The break timer shows "10:00" and counts down. This shows the user is in control, not locked into the default.

**Observable User States the Frontend Must Handle:**

- `idle` — No session running, "Start Session" button ready
- `session_running` — Timer counting down, session is active
- `session_complete_notified` — Session finished, notification visible, awaiting dismissal
- `break_starting` — Break timer is about to auto-start (very brief, mostly for state consistency)
- `break_running` — Break timer counting down, user is away from the desk
- `break_complete_notified` — Break finished, notification visible, "Start Next Session" button ready
- `break_skipped` — User chose to skip the break; go straight back to idle
- `break_extended` — User chose a custom break duration; timer counts down that duration instead

**Frontend Responsibilities:**

1. When a session completes and the backend has confirmed, extract completed_at
2. Automatically (without user click) show a break timer using the default break duration from settings
3. Use client clock to manage the break countdown
4. Allow the user to override: skip break, extend break, or wait for completion
5. On break timer reaching 0:00, show a notification: "Break complete! Ready for next session?"
6. The "Start Next Session" button should immediately POST /start for a new session
7. If settings are changed mid-break, apply the new break duration to the *next* break, not the current one
8. Handle offline: if the network drops during break, continue counting locally
9. Show error states if break completion or next session start fails

**Frontend-Backend Contract Points Exercised:**

- Session completion returns the full session record with completed_at timestamp
- Break timer starts immediately after session completion (no intermediate server call needed)
- POST /start for the next session uses the current settings (which may have been updated)
- Break duration comes from user settings; if not set, use default (5 minutes)
- A completed session with no /break-complete call still appears in history (break is optional)

**Failure Modes the Frontend Must Gracefully Handle:**

- Session complete notification arrives, but break timer doesn't auto-start → show "Preparing break..." spinner, retry
- User is offline when break completes → queue the "Break complete" acknowledgment; on reconnect, show history with break recorded
- User wants to extend the break mid-way → allow a "+" button to extend by 1 minute, or "Add time" option
- User dismisses the break timer notification and forgets about it → after 30 seconds of break timer showing 0:00 with no action, auto-show the "Ready for next session?" prompt
- Settings change during break → next break uses the new duration; current break is unaffected

**Expected Outcome:**

Yuki experiences the break as part of the natural rhythm. It's not a friction point; it's a built-in pause. She can rely on the timer, knows when she should get back to work, and can override it if needed. The rhythm feels intentional.

**When This Test Passes:**

The frontend successfully:
- Automatically transitions from session to break without user friction
- Maintains visible, reliable timers for both session and break
- Allows the user to customize or skip breaks when needed
- Records the break state (completed or skipped) without loss
- Handles offline, network, and settings-change scenarios gracefully
- Feels like a natural flow, not a series of disconnected screens
