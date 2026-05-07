## Ticket 003: Implement session state machine and transitions (backend)

**Sources:** start-and-complete-a-focus-session
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1.5–2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: implement-break-flow
- Blocked by: design-and-document-session-state-contract
- Soft: —

**Description:**

Backend: own the session lifecycle. Expose endpoints to create a session (POST /sessions), start it, pause it, complete it, begin a break, complete a break. Track elapsed time server-side (do not trust client clock). On start, record timestamp; on tick-from-client, validate elapsed time against server truth and respond with corrected elapsed. On complete, record completion timestamp and mark session done. Hard stop: no persistence across app restart in v1; no session history retrieval; no settings fetch/update.

**Acceptance:**
- POST /sessions creates a session in 'idle' state
- POST /sessions/{id}/start transitions to 'running' and records timestamp
- POST /sessions/{id}/pause transitions to 'paused'
- POST /sessions/{id}/complete transitions to 'complete' and records completion timestamp
- GET /sessions/{id} returns current state and elapsed time (corrected server-side)
- Unit tests on state machine cover all transitions and invalid-transition rejections

**Risk:**

Clock skew between client and server could cause elapsed time to jump. Mitigate by sending server-time on every tick response so client can resync.
