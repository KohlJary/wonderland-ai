## Contract Note 001: Session lifecycle and state machine

**State:** agreed
**Contract Version:** v1 (Frontend owns ephemeral timer. POST /api/sessions → 202 {session_id, started_at}. PATCH /api/sessions/{session_id} on expiry with {completed_at}. Abandoned sessions never persisted.)

**Current Shape:**

undefined

**Proposed Change:**

Backend maintains no persistent state during an active session. Frontend initiates session via POST /sessions/start (body: {duration_seconds: number}), receives immediate 202 response with {session_id, started_at}. Backend emits no further updates — the frontend owns the countdown timer. When frontend detects timer expiry, it POSTs /sessions/{session_id}/complete (body: {completed_at}). Backend validates completed_at is within expected range (started_at to started_at + duration + small jitter buffer), writes session record to database, returns 200 with the persisted record. If frontend never calls /complete, the session is abandoned and never persisted — no database cleanup needed, no 'incomplete session' record.

**Source:** ADR-001 (ephemeral vs persisted) and stories 001-002

**Frontend Impact (Tweedledee):**

Frontend owns the countdown timer (requestAnimationFrame-based, ephemeral state, lost on restart per ADR-001). Frontend initiates session via POST /sessions/start, receives {session_id, started_at}. Frontend runs local timer and detects expiry. On expiry, frontend POSTs /sessions/{session_id}/complete with {completed_at: timestamp}. Frontend does not expect live backend updates during countdown — the frontend timer is the source of truth. Frontend renders session UI (timer display, progress, 'session active' indicator) and transitions to break state on completion.

**Backend Impact (Tweedledum):**

Creates sessions table (id, user_id, created_at, started_at, completed_at, duration_seconds, nullable completed_break_at). No in-memory session state. Session write happens synchronously on /complete call. 202/200 responses are fast (< 10ms). No session query during countdown — frontend is the timer source of truth.

**Resolution:**

Unified v1 from Dum 001 + Dee 005. Locked.
