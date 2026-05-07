## Ticket 006: Persist session on completion

**Sources:** start-and-complete-a-focus-session
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.5-1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: session-history-daily-view
- Blocked by: session-record-schema, indexeddb-store, session-state-machine
- Soft: —

**Description:**

When a session reaches 'done' state, write the final record to IndexedDB. Include: start time, end time, actual duration, break count, session/break durations as they were configured at the time of the session. This is a contract between the state machine and persistence; the schema from ticket 1 defines what gets written.

**Acceptance:**
- Completed session is recorded to IndexedDB
- Record includes all required fields from schema
- Can retrieve the record later and verify accuracy

**Risk:**

None identified; this is straightforward once the schema and state machine are solid.
