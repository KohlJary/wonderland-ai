## Ticket 001: Implement session timer UI and start/stop controls

**Sources:** start-a-focus-session-and-receive-completion-notification
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–2 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: session-completion-notification, session-break-ui
- Blocked by: —
- Soft: session-timer-backend

**Description:**

Build the frontend components for initiating a focus session: a timer display showing remaining session time, a start button to begin the session, and a stop button to end early. The timer should update visually in real time. No persistence or notifications yet—just the interactive UI layer that lets the user control session flow.

**Acceptance:**
- Timer display is visible and readable
- Start button initiates a session state change
- Stop button ends the session state change
- Timer counts down in real time without lag
- UI is responsive on mobile and desktop

**Risk:**

Real-time timer updates can stutter on low-end devices; may need performance tuning. Synchronization between timer display and actual backend time may diverge if no handshake is in place.
