## Ticket 003: Implement timer and session state machine

**Sources:** start-and-complete-a-focus-session, take-a-timed-break-between-sessions
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1-2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: web-notification-implementation, session-ui-rendering
- Blocked by: session-record-schema
- Soft: —

**Description:**

Core session engine: a state machine (idle → running → break → running → done) driven by timers. Does not depend on persistence or UI. Pure logic: given a start time, current time, and user-configured durations, compute current state, time remaining, and transition events (end of focus session, end of break, etc.). Include: how do we handle the case where the user leaves the tab and comes back 3 hours later (does the timer catch up or do we reset), how do we preserve state across page reloads (this is where persistence and the engine meet).

**Acceptance:**
- State machine correctly transitions through idle → focus → break → focus → done
- Timer accurately computes time remaining
- Can serialize/deserialize state for persistence
- Handles tab-away-and-return gracefully (behavior TBD with Alice)

**Risk:**

Browser timer accuracy degrades when tabs are backgrounded; may need to fall back to server-side time if we add sync later. 1–2 day range depends on whether we handle clock-skew drift in v1 or defer.
