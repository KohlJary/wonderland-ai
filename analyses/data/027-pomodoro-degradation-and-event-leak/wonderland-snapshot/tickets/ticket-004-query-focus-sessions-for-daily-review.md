## Ticket 004: Query focus sessions for daily review

**Sources:** review-today-s-focus-sessions
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5-1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: persist-focus-session-to-indexeddb
- Soft: —

**Description:**

Implement read from IndexedDB to retrieve all focus sessions from the current day. Render a summary screen showing: count of completed sessions, total focus time (in hours:minutes), list of sessions with timestamps and durations. No filtering, sorting, or drill-down in MVP; just a flat list of today's sessions.

**Acceptance:**
- Daily review screen loads within 500ms
- Summary stats (count, total time) are accurate
- Session list includes start time and duration for each session
- Review screen refreshes when user returns from focus session

**Risk:**

Low. Data is simple; query is straightforward.
