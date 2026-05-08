## Ticket 002: Session length configuration: accept target duration on session creation

**Sources:** focus-session-timer
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.5 days, 85% confident
**Status:** open

**Dependencies:**
- Blocks: session-progress-frontend
- Blocked by: core-timer-state-machine
- Soft: —

**Description:**

Extend the state machine to accept and track a target session duration. Store it as part of session metadata. No enforcement yet — just acceptance and storage. The frontend will eventually use this to show progress and decide when to prompt for a break.

**Acceptance:**
- Create a session with target duration (e.g., 25 minutes)
- Target duration is stored and retrievable
- State machine accepts the duration without breaking elapsed tracking

**Risk:**

Low. This is additive to the existing state shape.
