## Ticket 002: Implement session timer backend and state management

**Sources:** start-a-focus-session-and-receive-completion-notification
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1.5–2.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: session-completion-notification, break-timer-backend, session-history-query
- Blocked by: —
- Soft: —

**Description:**

Build the backend session lifecycle: track session start time, elapsed time, and session state (active/paused/completed). Store the session record in the database with timestamps. Expose an API endpoint that returns current session status and remaining time. This is the source of truth for session timing; the frontend timer UI will poll or subscribe to this.

**Acceptance:**
- Session can be created with a configurable duration
- Session state transitions are tracked (active → completed or stopped)
- API endpoint returns current elapsed time and remaining time
- Session record is persisted with creation and completion timestamps
- Multiple rapid start/stop calls do not corrupt state

**Risk:**

Clock skew between client and server could make the timer feel unreliable; consider server time as authoritative. Database write latency on session completion could delay the completion notification.
