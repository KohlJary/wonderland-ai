## Ticket 002: Build focus session timer UI and lifecycle

**Sources:** start-and-run-a-focus-session
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1-1.5 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: break-timer-ui
- Blocked by: persistent-storage
- Soft: session-history-list

**Description:**

Implement the user-facing focus session UI: start button, running timer display (mm:ss format), pause/resume/stop controls, and visual feedback for session state. Coordinate with backend on session event emission so UI stays in sync with data persistence. The timer itself is client-side; the backend persists the completed session record. Keep the UI minimal — the persona here is someone who wants to *start* a session and have it *work*, not someone hunting through menus.

**Acceptance:**
- User can start a focus session and see a running timer
- Timer display updates every second
- User can pause and resume the running session
- User can stop and end the session (triggers break prompt)
- Session state reflects in the UI immediately on state change

**Risk:**

Timer precision on lower-end mobile devices; if accuracy becomes an issue, may need platform-specific timer handling (1 day additional). Test timer drift under 10+ minute sessions.
