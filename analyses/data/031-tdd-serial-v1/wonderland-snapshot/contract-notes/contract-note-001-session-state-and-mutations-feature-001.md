## Contract Note 001: Session State and Mutations (Feature 001)

**State:** agreed
**Contract Version:** v1 (POST /api/sessions/start {duration_seconds: int} -> {session_id UUID, elapsed_ms int, status enum, created_at ISO8601Z}, GET /api/sessions/<id> -> current state, POST .../pause|resume|skip idempotent, wall-clock elapsed, completion_type enum)

**Current Shape:**

none

**Proposed Change:**

Frontend needs a session state object with real-time elapsed counter, plus methods to start/pause/resume/skip a session. The session state is the foundation for features 001 and 002. Session completion triggers event logging (for feature 003's daily review).

**Source:** story-001 (visual countdown, audio alert on completion), story-002 (break timer auto-start after focus completion)

**Frontend Impact (Tweedledee):**

UI renders countdown from elapsed_ms. UI implements pause/resume/skip buttons with state-dependent visibility. UI plays audio+visual alert on completion. UI must handle real-time updates (smooth tick, not jittery). UI is responsible for calculating visual representation (MM:SS format). Session state is ephemeral (not persisted locally or to backend); page reload starts fresh. UI plays alert only if completion_type='timeout' (skip does not trigger alert).

**Backend Impact (Tweedledum):**

Sessions are server-side ephemeral state (in-memory dict keyed by session_id UUID during v1; may migrate to database if feature 003 requires historical query). POST /api/sessions/start with {duration_seconds: int} returns {session_id: UUID, duration_seconds: int, created_at: ISO8601Z, status: 'running', elapsed_ms: 0}. GET /api/sessions/<session_id> returns current state with elapsed_ms computed as (now - created_at) milliseconds, as integer. Session status states: 'running' (timer advancing), 'paused' (elapsed frozen), 'completed' (terminal). Transitions: running→paused (via POST /api/sessions/<id>/pause), paused→running (via POST /api/sessions/<id>/resume), running|paused→completed (via POST /api/sessions/<id>/skip or timeout). Pause stores pause_at timestamp and frozen_elapsed_ms; resume unfreezes. Skip sets completion_type='skip' and completed_at (ISO8601Z). Timeout (when elapsed ≥ duration, auto-completed by frontend or via a test endpoint in M5) sets completion_type='timeout'. Elapsed time must be wall-clock-based (computed from timestamps), not tick-count, so sessions continue advancing when client is hidden. Paused sessions are not auto-resumed and do not persist across page reload. Validation: duration_seconds > 0 (reject 0 and negative), session_id must be valid UUID on operations, timestamps valid ISO8601. Idempotency: second pause returns 200 with no state change (idempotent), second resume returns 200 with no state change, second skip returns 200 with no state change. Session completion does not log an event in v1 (event logging deferred to feature 003).

**Resolution:** pending agreement

**Resolution:**

Backend impact is detailed and matches test surface. All three of Tweedledee's unknowns are resolved in the contract. Locking v1.
