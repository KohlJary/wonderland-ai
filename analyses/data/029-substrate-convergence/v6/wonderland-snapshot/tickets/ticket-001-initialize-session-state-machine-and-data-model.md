## Ticket 001: Initialize session state machine and data model

**Sources:** start-and-complete-a-focus-session
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1–2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: session-ui-start-button, session-ui-complete-button, session-review-query
- Blocked by: —
- Soft: —

**Description:**

Define the session entity (id, start_time, end_time, duration_target, is_active, created_at). Define the break entity with parallel shape. Implement state transitions: idle → active (on session start), active → completed (on session end). Persist to the backing store. No UI yet; this is schema + state logic only.

**Acceptance:**
- Session can transition from idle → active → completed
- All state changes are persisted
- Breaking the state machine (e.g., completing when not active) is rejected

**Risk:**

If the backing store choice (in-memory vs. persistent DB) is undefined, this will stall. Assume persistent for v1 scope.
