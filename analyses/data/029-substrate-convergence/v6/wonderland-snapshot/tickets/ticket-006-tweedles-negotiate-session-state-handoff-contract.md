## Ticket 006: Tweedles: negotiate session state handoff contract

**Sources:** start-and-complete-a-focus-session, review-today-s-completed-sessions
**Owner:** tweedledee, tweedledum
**Tier:** v1
**Estimate:** 0.5 days, 85% confident
**Status:** open

**Dependencies:**
- Blocks: session-ui-start-button, session-ui-complete-button, review-sessions-endpoint, review-sessions-ui
- Blocked by: session-state-machine
- Soft: —

**Description:**

The Tweedles sync on the exact shape of the request/response for session start, session complete, and today's sessions fetch. Define: request payloads (parameters), response shapes (fields, types), error cases (what happens if you try to complete a session that was never started), and the refresh semantics (does the UI poll, or does it rely on optimistic updates?). Capture this as a contract note.

**Acceptance:**
- A contract note exists on disk
- Contract specifies request/response shapes for all three interactions
- Both Tweedles have acknowledged the contract

**Risk:**

If the contract is vague on timing (e.g., when the timer should update), the implementation will drift. Be explicit about polling intervals or event-driven updates.
