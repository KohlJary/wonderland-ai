## Ticket 003: Break timer state machine: countdown from break duration

**Sources:** break-timer-between-sessions
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.75–1.25 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: break-timer-frontend
- Blocked by: session-persistence-backend
- Soft: —

**Description:**

A second state machine, separate from the focus session machine, that counts down from a break duration (e.g., 5 minutes). Similar shape: start/pause/stop, elapsed tracking, but the semantic is a countdown. Expose via API contract. Store break state alongside session state.

**Acceptance:**
- Start a break with duration; counter decrements from duration to zero
- Pause/resume work as expected
- Stop finalizes the break
- Break state persists across restarts

**Risk:**

If the focus and break machines end up sharing too much state, we may want to unify them. That refactor is post-v1.
