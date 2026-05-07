## Ticket 001: Define session record schema and persistence contract

**Sources:** start-and-complete-a-focus-session, take-a-timed-break-between-sessions, adjust-session-and-break-durations
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5-1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: session-engine-implementation, session-history-persistence, session-ui-rendering
- Blocked by: —
- Soft: —

**Description:**

Specify the shape of a session record (start time, end time, break count, session duration setting at time of record, break duration setting at time of record). Document in code as a TypeScript interface or Zod schema. This is the contract that both frontend and backend reference; it must exist before feature work begins. Include: what fields are user-editable after logging, what fields are immutable, how do settings changes get versioned if at all in v1.

**Acceptance:**
- Schema is defined as code (TypeScript interface or Zod)
- Fields documented: immutable, user-editable, derived
- At least one example record shown in comments
- No breaking changes to schema without ADR follow-up

**Risk:**

If schema design is unclear (e.g., do we version settings retroactively or store them per-session), this ticket can expand to 1.5 days.
