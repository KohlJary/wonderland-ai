## Ticket 003: Persist focus session to IndexedDB

**Sources:** start-and-complete-a-focus-session, review-today-s-focus-sessions
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1-1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: query-focus-sessions-for-daily-review
- Blocked by: —
- Soft: initialize-focus-session-with-user-set-duration, render-focus-session-completion-screen

**Description:**

Design and implement local IndexedDB schema to store focus sessions. Schema must support: session ID (UUID), start time, target duration, actual duration, completion status, persona tag (if applicable), break taken (boolean). Implement write operation on session initiation and completion. No server calls in M1; this is purely local persistence.

**Acceptance:**
- IndexedDB schema is defined and migrated on app load
- Session write succeeds within 100ms of user action
- Session records persist across browser restarts
- Schema includes version field for future migrations

**Risk:**

IndexedDB quota and error handling could expand scope. MVP: no quota warnings; assume quota is sufficient for v1 (< 100 sessions).
