## Ticket 005: Build session UI: timer display and controls

**Sources:** start-and-complete-a-focus-session
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1.5-2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: session-history-daily-view
- Blocked by: session-state-machine, indexeddb-store, web-notification-implementation
- Soft: —

**Description:**

Render the timer, current state, and controls (start, pause, skip break, stop session). Display must update once per second while a session is running. Wired to the session state machine; reads from persistence. Does not include history rendering, settings, or export — those are separate tickets. Keep the UI simple: show the timer, show the state, offer the meaningful buttons.

**Acceptance:**
- Timer displays and updates in real time
- Current state (focus / break / done) is visible
- Start, pause, and stop buttons work
- Survive a page reload without losing state

**Risk:**

High-frequency DOM updates (once per second) can cause jank if not optimized. May need to batch state updates or use requestAnimationFrame.
