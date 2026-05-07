## Test Scenario 005: Marcus starts and completes a focus session (User Journey)

**Feature:** Start and complete a focus session (feature-001)
**Persona:** Marcus, 34, software engineer working from home. Uses timers to force focus.
**Stack span:** frontend + backend
**Severity:** critical
**Concern:** User happiness — does the core interaction work smoothly for the real user Marcus?

**User Journey:**

Marcus opens the app. He sees a clean interface with a large "Start Session" button and the default 25 minutes displayed. He taps "Start Session."

The button changes to a timer showing "25:00" and begins counting down. Marcus switches to his code editor and starts working on the refactor. He glances at the app in his peripheral vision occasionally to check how much time is left.

After 24:17, the timer has visibly counted down. Marcus is deep in the problem and doesn't notice when it hits 0:00. The app plays a notification sound and shows a banner: "Session complete!" with a satisfying visual flourish (a checkmark or color shift). Marcus glances at the app, sees the notification, and dismisses it with a tap.

The timer disappears. The interface resets to show the "Start Session" button again, and Marcus notices a new badge on his screen: "1 session today."

Marcus taps on "Today" to see his progress, and he sees a list showing: "Session 1: 25 minutes, completed at 2:47 PM." The session is recorded.

**Observable User States the Frontend Must Handle:**

- `idle` — The "Start Session" button is ready, default durations visible, previous sessions listed if any
- `loading` — "Start Session" is tapped but the backend hasn't confirmed yet (rare, but the frontend should show a brief spinner)
- `session_running` — Timer is counting down, user is focused on work, the app is minimized/background but timer is visible (via notification area or persistent widget if possible)
- `session_complete_notified` — Notification has arrived, banner visible, user hasn't dismissed yet
- `session_complete_acknowledged` — User has dismissed the notification, interface returns to idle
- `offline` — If the network is poor or the user is offline, the session should still time locally; when reconnected, the completion is submitted

**Frontend Responsibilities:**

1. Start button initiates a POST /start request
2. On 202 response, extract session_id and started_at from the response
3. Use the client clock (not server time) to manage the countdown timer
   - Calculate: now + duration_seconds = expected_completion
   - Decrement visible timer every 1 second
4. When local timer reaches 0:00, show notification and sound
5. When user dismisses notification (or after a timeout), call PATCH /complete with the completion timestamp
6. On success, increment the "Today" count and return to idle
7. If offline, queue the /complete call; on reconnect, retry and update history
8. Show error state if the completion fails (e.g., 400 Bad Request from backend)

**Failure Modes the Frontend Must Gracefully Handle:**

- Backend returns error on /start → show "Failed to start session" and retry button
- Backend returns error on /complete → queue the completion locally and retry on network recovery
- Network drops mid-session → continue counting down locally; submit completion when reconnected
- User closes app mid-session → on reopening, restore the session state (still running or completed?)
- User receives a phone call during session → timer should be accessible without bringing app to foreground (depends on platform capability)

**Expected Outcome:**

Marcus completes his first focus session with minimal friction. The timer was visible when he needed it, the notification was clear, and the session was recorded. He's ready to start another one immediately.

**When This Test Passes:**

The frontend successfully:
- Displays an interactive timer that the user can rely on
- Handles the session lifecycle from start to completion
- Records sessions in history without loss
- Handles offline and network-error conditions gracefully
- Feels responsive and intentional to the user (no unexplained delays or state confusion)
