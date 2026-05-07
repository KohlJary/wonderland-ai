## Contract Note 001: Session lifecycle & timer state

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

N/A — proposing initial contract

**Proposed Change:**

Session entity with start_time (UTC), duration (minutes, configurable), state (active|paused|completed), completed_at (UTC, null until completion). API endpoint /session/current returns {id, state, start_time, elapsed_seconds, remaining_seconds}. Server time is authoritative for elapsed/remaining. State transitions: active→paused→active (pause/resume), active→completed (timeout), active→completed (manual stop). Manual stop or timeout both trigger completion. All writes are idempotent — duplicate start requests are no-ops (return existing session), duplicate stop requests are no-ops.

**Source:** Feature 001 (start session, timer, notification); tickets 001-003

**Frontend Impact (Tweedledee):**

Client-side timer display requires reconciliation with server time. On /session/current response, client caches {start_time, remaining_seconds}. Client computes local elapsed via (now_client - start_time) and updates remaining = max(0, remaining_seconds - elapsed). Local clock drift is bounded: if client remaining diverges >5s from server remaining on next poll, client re-syncs to server time (prevents drift accumulation).

Client state (session store): {sessionId, state, start_time, remaining_seconds, duration_minutes}. This state persists for the life of the active session; cleared on session→completed.

UI states: loading (fetching /session/current), active (timer running, display remaining), paused (timer paused, display remaining + resume button), completed (session ended, display completed_at). Error states: offline-queued (pause/stop request queued, pending sync), error-recoverable (API error on start/stop, user can retry).

Timer display refreshes every 100ms client-side (smooth countdown). Network polls for server state every 5s to detect timeout or server-initiated completion.

Open question for pair: Does server enforce max pause duration, or can a session be paused indefinitely? If indefinite, client needs to handle "paused for N hours" display.

**Backend Impact (Tweedledum):**

Sessions table: user_id FK, start_time UTC, duration_minutes, state enum (active|paused|completed), completed_at UTC nullable, paused_at UTC nullable, pause_duration_total_seconds. Max pause duration enforced: server rejects pause requests if cumulative pause exceeds 6 hours. State machine: active→paused, paused→active, active→completed (timeout or manual), paused→completed. Idempotency: session creation keyed by (user_id, start_date); duplicate requests return 409 if session active. Pause/resume/stop idempotent by requestId. Timer endpoint /session/current returns {id, state, start_time, elapsed_seconds, remaining_seconds, paused_duration_seconds}. Server time is authoritative.
