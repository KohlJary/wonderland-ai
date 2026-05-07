## Ticket 003: Timer state machine and session lifecycle (backend)

**Sources:** story:start-and-complete-a-focus-session, story:take-and-track-a-break
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1–1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: ticket:frontend-timer-ui-and-session-rendering
- Blocked by: ticket:define-session-state-machine-and-contract-for-timer-history-seam, ticket:schema-and-migrations-for-timer-and-history
- Soft: ticket:settings-read-and-write-endpoints (needs to read session_length, break_length on startup)

**Description:**

State machine: idle → running → paused → completed (or break_running → break_completed). Endpoints: POST /session (start timer), PATCH /session (pause/resume), GET /session (current state). On session completion, write atomically to both sessions (mark completed) and session_history (append log). Return completion event payload that Frontend can consume.

**Acceptance:**
- POST /session creates a new session in running state, returns session_id and countdown_ms
- PATCH /session?action=pause pauses the timer (state → paused), PATCH ?action=resume resumes
- PATCH /session?action=complete marks session as completed, writes to session_history in same transaction
- GET /session returns current session state (running, paused, idle, or 404 if no active session)
- Session completion response includes session_id, duration, type (focus or break), timestamp
- State machine rejects invalid transitions (can't resume from idle, can't complete a paused session without running it first, etc.)

**Risk:**

Crash-safety of the session→history write. If app crashes mid-transaction, session is lost. Mitigate by testing crash scenarios in acceptance or by picking transaction pattern in contract ticket.
