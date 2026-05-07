## Ticket 001: Implement Pomodoro timer UI and state machine

**Sources:** start-and-complete-a-focus-session, take-a-break-and-return-to-focus
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: wire-timer-state-to-persistence, add-session-history-view
- Blocked by: —
- Soft: —

**Description:**

Build the visual timer display, start/pause/stop controls, and session-state transitions (idle → running → break → running → complete). Include visual feedback for session phase (focus vs break). Do not wire to backend yet; use local state. Focus on the user's perception of time passing and their ability to control the current session.

**Acceptance:**
- User can start a 25-minute focus session and see the timer count down
- User can pause and resume the current session
- User can stop the session (ends early)
- When a focus session completes, the UI transitions to break phase automatically
- Break timer counts down; when complete, returns to idle (ready for next session)
- Visual indication of which phase is active (focus vs break)

**Risk:**

Pause/resume across page refresh may require a quick check with backend; defer to next ticket if it arises.
