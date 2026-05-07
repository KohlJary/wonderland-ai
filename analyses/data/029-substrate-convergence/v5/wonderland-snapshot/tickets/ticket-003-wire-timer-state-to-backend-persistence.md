## Ticket 003: Wire timer state to backend persistence

**Sources:** trust-the-app-to-retain-data-across-sessions, start-and-complete-a-focus-session
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1.5–2.5 days, 60% confident
**Status:** open

**Dependencies:**
- Blocks: add-session-history-view
- Blocked by: —
- Soft: implement-pomodoro-timer-ui-and-state-machine, implement-customizable-session-and-break-lengths

**Description:**

Create backend endpoints to store and retrieve session state (in-progress session, completed sessions, user settings). When user starts/completes a session on frontend, POST to backend. On app load, fetch in-progress session and resume from where it left off (if exists). Store completed sessions with timestamps. This is the backbone of data retention across browser sessions.

**Acceptance:**
- User can start a session; state is persisted immediately
- User closes browser and returns; in-progress session resumes from remaining time
- Completed sessions are stored with date/time
- User settings (custom lengths) are persisted and loaded on app startup
- Backend returns 400-level errors gracefully (frontend falls back to localStorage)

**Risk:**

If authentication is required, this ticket expands significantly. Assume unauthenticated user for v1; revisit if scope includes login.
