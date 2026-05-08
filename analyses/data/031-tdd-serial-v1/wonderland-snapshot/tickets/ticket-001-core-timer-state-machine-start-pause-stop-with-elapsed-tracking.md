## Ticket 001: Core timer state machine: start/pause/stop with elapsed tracking

**Sources:** focus-session-timer
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: focus-session-timer-frontend, session-persistence-backend
- Blocked by: —
- Soft: —

**Description:**

Backend state machine for a single focus session. Tracks elapsed time, handles start/pause/stop transitions, persists session state to storage. No UI yet. Expose via an API contract (shape TBD with Tweedledee). The machine does not care about session length or breaks — it is pure elapsed-time tracking with state semantics.

**Acceptance:**
- Start a session; elapsed time increments at 1 sec/sec
- Pause stops elapsed increments; resume resumes from paused value
- Stop finalizes the session and closes state
- State survives a process restart (persisted to disk/DB)

**Risk:**

If storage layer is not yet available, build an in-memory shim first; we'll swap it for real storage in the persistence ticket.
