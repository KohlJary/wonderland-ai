## Ticket 005: Frontend: today's sessions review card

**Sources:** review-today-s-completed-sessions
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: review-sessions-endpoint
- Soft: —

**Description:**

Display a 'Today's Sessions' section below the active-session area. Fetch from the review endpoint. Show each session as a card with: start time, end time, duration, and a visual indicator (checkmark for completed). Order by most recent first. No aggregation, no charts — just a list.

**Acceptance:**
- Sessions list appears after at least one session is completed
- Each session shows start, end, duration, completion status
- List is ordered by most recent first
- List updates when a new session is completed (no manual refresh required)

**Risk:**

List refresh timing: need to clarify whether the list refreshes automatically after completing a session or requires a manual fetch. Assume automatic for v1; the backend-to-frontend handoff will clarify in contract negotiation.
