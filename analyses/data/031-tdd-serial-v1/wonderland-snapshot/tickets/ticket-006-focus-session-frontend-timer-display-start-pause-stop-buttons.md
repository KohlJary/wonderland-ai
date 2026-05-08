## Ticket 006: Focus session frontend: timer display, start/pause/stop buttons

**Sources:** focus-session-timer
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: session-complete-backend
- Blocked by: core-timer-state-machine
- Soft: —

**Description:**

User-facing UI for the focus session. Display elapsed time (MM:SS), show target duration as a progress indicator or visual bar. Buttons: Start, Pause, Stop. When a session is running, the UI updates at 1 Hz. When stopped, prompt user to confirm if they want to save the session or discard. Bind to the backend state machine via the API contract Tweedledum defines.

**Acceptance:**
- User starts a focus session; timer increments on-screen
- User pauses; timer stops; resume resumes it
- User stops; prompted to save or discard
- Session elapsed time is readable at a glance

**Risk:**

Timer synchronization with backend. If the connection drops while a session is running, the frontend must handle graceful reconnect. For v1, assume solid connection; add offline resilience in fast-follow.
