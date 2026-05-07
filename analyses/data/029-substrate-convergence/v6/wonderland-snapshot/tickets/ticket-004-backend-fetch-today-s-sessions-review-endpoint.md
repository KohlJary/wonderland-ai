## Ticket 004: Backend: fetch today's sessions (review endpoint)

**Sources:** review-today-s-completed-sessions
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: review-sessions-ui
- Blocked by: session-state-machine
- Soft: —

**Description:**

Implement a GET endpoint that returns all sessions created today, ordered by start_time descending. Include id, start_time, end_time, duration (computed), and is_completed. Filter by the current user. No aggregation yet; just the raw list.

**Acceptance:**
- Endpoint returns all of today's sessions for the authenticated user
- Sessions are ordered by start_time descending
- Each session includes computed duration (end_time - start_time)
- Completed sessions are clearly marked

**Risk:**

If session timestamps are ambiguous about timezone or if 'today' logic is user-timezone-dependent, this will require careful handling. Clarify timezone assumptions.
