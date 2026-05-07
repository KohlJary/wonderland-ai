## Contract Note 004: Break state and break-to-session transition

**State:** agreed
**Contract Version:** v1 (Break is completed_break_at property on session record, nullable. POST /sessions/{session_id}/break-complete with {completed_at} returns full updated session record. Frontend owns break timer state; backend records completion.)

**Current Shape:**

undefined

**Proposed Change:**

Break is not a separate entity in the database; it's an optional property on a session record (completed_break_at timestamp). When a session completes, frontend shows break UI automatically (per story 002 acceptance). Frontend counts down the break timer locally (same as session timer — ephemeral, frontend-owned). When user completes the break or clicks 'start next session', frontend POSTs /sessions/{previous_session_id}/break-complete (body: {completed_at}) to record that the break finished, then starts a new session via POST /sessions/start as normal. The break-complete call is synchronous; it updates the previous session's completed_break_at field.

**Source:** Story 002 (automatic break prompt) and feature 002

**Frontend Impact (Tweedledee):**

Conceding your model — break as completed_break_at property on the session record is the right call for maintaining the invariant. Frontend tracks break state separately (break_started_at, break_elapsed_ms, break_duration_ms in React state, ephemeral). On break completion, frontend POSTs /sessions/{session_id}/break-complete with {completed_at}. Two clarifications needed: (1) Does completed_break_at accept null initially, then get populated on break-complete? (2) Should break-complete return the updated session record, or just 200 OK? I need the full session record back so I can validate the write succeeded.

**Backend Impact (Tweedledum):**

Sessions table extended with nullable completed_break_at. Break-complete endpoint is a single-field update (fast). No separate break record. Break is implicit in the session record's completed_break_at presence.

**Resolution:**

completed_break_at starts null, gets populated on break-complete. Endpoint returns full updated session record for client validation. Frontend tracks break state in React (ephemeral); backend persists completion timestamp only.
