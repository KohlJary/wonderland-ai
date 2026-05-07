## Ticket 004: Implement break timer UI and state transitions

**Sources:** take-a-break-and-prepare-for-the-next-session
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: session-completion-notification
- Soft: break-timer-backend

**Description:**

Build the frontend UI for the break period: a timer display showing remaining break time, a skip button to end the break early and start a new session, and a way to dismiss the break notification when it completes. The break timer should mirror the session timer in UX—same visual style, same real-time countdown.

**Acceptance:**
- Break timer appears after session completion
- Timer counts down to zero without stutter
- Skip button allows user to skip the break and start a new session
- Break timer notification appears when break completes
- UI is visually consistent with session timer

**Risk:**

Same performance considerations as session timer. May need to handle rapid skip-and-start sequences.
