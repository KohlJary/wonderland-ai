## Contract Note 004: Session state mutations: start, complete, abandon

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

undefined

**Proposed Change:**

Define POST /sessions (start), PATCH /sessions/{id}/complete (end), DELETE /sessions/{id} (abandon). Each returns session object with id, start_time, end_time, duration_target, is_active, is_completed, created_at, updated_at.

**Source:** Features 001, 002, 006; Ticket 006 explicitly names this as blocking.

**Frontend Impact (Tweedledee):**

Frontend can initiate session lifecycle (start → complete → list view). Timer needs server-provided elapsed time on fetch to avoid client drift. State transitions are explicit: start returns is_active=true; complete returns is_completed=true, is_active=false; abandon returns is_deleted=true (soft delete) or removes the session.

**Backend Impact (Tweedledum):**

Three endpoints: POST /sessions/start (creates, returns 201), POST /sessions/{id}/complete (transitions, returns 200), DELETE /sessions/{id} (soft delete, returns 204). Abandon: DELETE sets is_deleted=true (soft delete, not removed from DB) so history is preserved if user later wants analytics. Returns 204 No Content (idempotent). Invariant: all three endpoints are idempotent; resending the same request produces the same state. Start conflict returns 409; complete/abandon on already-deleted returns 404. State enum doesn't need explicit column; is_active/is_completed/is_deleted bools are sufficient. No explicit 'pending' state — sessions start active immediately.
