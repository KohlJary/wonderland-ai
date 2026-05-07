## Ticket 001: Design and document session-state contract

**Sources:** start-and-complete-a-focus-session
**Owner:** Tweedledee & Tweedledum (joint)
**Tier:** v1
**Estimate:** 1–2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: implement-session-timer-ui, implement-session-state-backend, implement-break-flow
- Blocked by: —
- Soft: adjust-session-and-break-lengths

**Description:**

Align on the shape of a focus session object: what fields (duration, elapsed, state, timestamps, break-info), what state transitions (idle → running → paused → complete → break → idle), what events both sides need to observe (start, tick, complete, break-start, break-complete). This contract lives in the M3 thread; ship it in the first two days so both Tweedles can start implementation against a stable target.

**Acceptance:**
- Contract document (Markdown or schema) lives in codebase with explicit field definitions and state-machine diagram
- Both Tweedles have acknowledged the contract and confirmed they can implement against it
- Contract names what happens on app restart (v1 scope: in-progress sessions are lost; fast-follow: resumed)

**Risk:**

If the Tweedles discover mid-implementation that the contract is missing a field (e.g., session-start-time), rework ripples both ways. Front-load clarity.
