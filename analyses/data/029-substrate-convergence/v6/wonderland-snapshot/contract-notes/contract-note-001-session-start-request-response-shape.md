## Contract Note 001: Session Start Request/Response Shape

**State:** agreed
**Contract Version:** v1 (session POST with 1-active invariant)

**Current Shape:**

(none yet — first draft)

**Proposed Change:**

POST /sessions/start — request is empty; response is {id, session_id, start_time, target_duration_seconds, current_elapsed_seconds}. Backend creates a session entity, transitions state to active, persists it. Returns the session object with server-provided timing so client doesn't drift.

**Source:** story-001 (start-and-complete-a-focus-session) + ticket-002 (frontend-session-start-button-and-timer-display)

**Frontend Impact (Tweedledee):**

Frontend receives {id, start_time, target_duration_seconds, current_elapsed_seconds}. Uses this to initialize the timer display with server-provided start_time as the canonical reference point (not client's local time). Stores in client state: active session {id, start_time, target_duration_seconds}. Timer runs locally using relative ticks (Date.now() - start_time) to avoid repeated server queries while session is active. On receipt of response, transitions UI to "timer-running" state. Timing constraint: response latency should be <2s for UX (user starts session, sees timer begin within ~2s). No retry needed on 409 conflict — frontend picks up existing session id from response and resumes timer from that session's start_time.

**Backend Impact (Tweedledum):**

Sessions table: id (uuid), user_id (FK), start_time (server-provided NOW()), end_time (nullable), target_duration_seconds (from user config or default 1500), is_active (bool, starts true), is_completed (bool, starts false), created_at, updated_at. Constraint: (user_id, is_active) unique partial index on is_active=true ensures one active session per user. POST /sessions/start returns 201 with {id, start_time, target_duration_seconds, is_active: true, created_at}. On conflict (user already has active session), return 409 with existing session object so client can pick it up (idempotent). Never allow client to specify start_time; prevents clock drift abuse.

**Resolution:**

Agreed. One-active-session invariant enforced by partial unique index. Start time is server-provided (no client clock input). Conflict returns 409 with existing session, allowing client to recover gracefully.
