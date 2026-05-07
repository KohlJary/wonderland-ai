## Contract Note 008: Break state and session-to-break transition

**State:** agreed
**Contract Version:** v1 (Break is completed_break_at property on session record, nullable. POST /sessions/{session_id}/break-complete with {completed_at} returns full updated session record. Frontend owns break timer state.)

**Current Shape:**

No contract yet; establishing baseline

**Proposed Change:**

When a session completes, frontend transitions to 'break' state (another ephemeral timer). Break state is separate from session state; frontend tracks break_started_at, break_elapsed_ms, break_duration_ms. On break completion, frontend returns to idle (ready for next session). Break is *not* persisted until the user explicitly completes it (or the next session is started). Semantics: a break is a transition between sessions, not a persisted 'break record'.

**Source:** feature-002 (take a break and return to focus)

**Frontend Impact (Tweedledee):**

Confirm: break_started_at governs your countdown timer, break_recorded_at is observability only?

**Backend Impact (Tweedledum):**

Session record carries break_started_at (when break event fired, owned by timer) and break_recorded_at (when the write persisted). Frontend timer computes break_remaining from break_started_at, not break_recorded_at — network lag doesn't shift the visible countdown. Break status property is boolean (true = active break, false = active session).

**Resolution:**

Unified v1 from Dum 004 + Dee 008. completed_break_at=null initially, populated on break-complete. Endpoint returns full session record for client validation. Locked.
