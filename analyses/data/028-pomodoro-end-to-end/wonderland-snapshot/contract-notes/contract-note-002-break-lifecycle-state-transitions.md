## Contract Note 002: Break lifecycle & state transitions

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

N/A — proposing initial contract

**Proposed Change:**

Break state is transient and coupled to Session lifecycle. When session completes (state=completed, completed_at set), backend automatically initializes a break with start_time and configurable duration (from user Settings). Break state (active|skipped|completed) is tracked in session_break records or as fields on Session. API endpoint /break/current returns {id, state, start_time, elapsed_seconds, remaining_seconds, skip_available}. User can skip break via /break/skip, which sets state=skipped and marks session ready for next. Both skip and timeout transition to completed and return next session trigger. Skip during completion (race) handled by idempotency: skip request is idempotent, last-write-wins.

**Source:** Feature 002 (break timer, next session); tickets 004-005

**Frontend Impact (Tweedledee):**

Client waits for session→completed signal, then immediately polls /break/current. Break state follows same client-side timer reconciliation as session: client caches {start_time, remaining_seconds}, computes local elapsed, syncs with server every 5s.

Client state (break store): {breakId, state, start_time, remaining_seconds, duration_minutes, skip_available}. State clears on break→completed or break→skipped.

UI states: loading (transitioning from session complete to break screen), active (break timer running, display remaining + skip button), skipped (user tapped skip, awaiting next session), completed (break time elapsed, display "ready for next session" + start button). Error states: error-recoverable (skip failed, user can retry).

Open questions for pair:
1. When session completes, is break automatically started on backend, or does client request /break/current and backend creates break on-demand?
2. Does skip_available depend on user Settings, or is it always true in v1?
3. After break→completed or break→skipped, what does frontend see from /break/current? Error, or empty break entity? (Affects error handling.)
4. If break timeout fires server-side before client polls, does /break/current return state=completed, or is there a separate timeout notification?

**Backend Impact (Tweedledum):**

Break created automatically on session→completed transition. Breaks table: user_id FK, session_id FK (not nullable), start_time UTC, duration_minutes, state enum (active|skipped|completed), completed_at UTC nullable. State machine: active→skipped, active→completed (timeout), skipped→completed (immediate). Skip endpoint idempotent by breakId. Client polls /break/current every 5s; after break ends, returns 404 or {state: 'no_active_break'} (Tweedledee confirms pattern). Timeout delivery: if break times out server-side before poll, /break/current returns {state: 'completed', completed_at: <timestamp>}.
