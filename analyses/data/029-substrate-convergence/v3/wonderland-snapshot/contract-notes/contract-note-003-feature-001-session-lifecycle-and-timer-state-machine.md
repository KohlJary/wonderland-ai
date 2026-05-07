## Contract Note 003: Feature 001: Session lifecycle and timer state machine

**State:** counterpart_assessed
**Contract Version:** v1 (Session state machine: new|running|paused|completed; SessionRecord atomic write on completion; WebSocket state subscription; frontend timer reconciliation on state update; break as explicit new session; completion event ordering: SessionRecord write → completion event → frontend UI transition)

**Current Shape:**

none yet

**Proposed Change:**

Backend persistence: Session table (id, status enum [idle|running|paused|completed], session_length_minutes, break_length_minutes, started_at, paused_duration_ms, completed_at). On session completion, atomically write a SessionRecord (completed_at, session_duration_ms, break_duration_ms, session_type enum [focus|break]) and set Session.status = completed. Clients poll or subscribe (WebSocket) to Session.status changes. On break completion, reset Session.status = idle, allowing new session start.

**Source:** Feature 001: Run a focused work session with built-in break

**Frontend Impact (Tweedledee):**

Frontend manages UI state machine: `idle` (show start button), `running` (show countdown timer, pause button), `paused` (show resume/abandon buttons), `completed` (show break countdown, skip button, auto-transition to break). 

Client-side timer display: frontend holds transient countdown (elapsed seconds) updated every 100ms by setInterval, not the canonical duration. On every Session.status message from backend, frontend resets its local elapsed to match the server's (started_at + current time - paused_duration). Clock drift >1s triggers a hard reset (corrects for user's device clock being off). Pause-duration accumulation: frontend doesn't calculate this — backend tracks paused_duration_ms cumulatively, frontend just displays the current countdown derived from (session_length_minutes × 60 - elapsed - paused_duration_ms).

UI state transitions are deterministic from Session.status: idle→idle (already idle, show start), idle→running (start pressed, countdown begins), running→paused (pause pressed), paused→running (resume pressed), running/paused→completed (countdown reached zero or explicit complete), completed→idle (auto-transition after break countdown, or user dismisses break).

Client state: only transient timer display (elapsed_seconds). No session record stored on client. On app restart or WebSocket reconnect, frontend immediately queries /api/session (or receives via subscription) to learn current Session.status and resumes from there. If status is `completed`, show break UI; if `running`, show countdown; if `idle`, show start button.

**Backend Impact (Tweedledum):**

Session table enforces state machine (idle|running|paused|completed) with transactional validation. On pause: Session.paused_duration_ms incremented atomically (tracks cumulative pause time across the session). On completion: atomic transaction writes SessionRecord (session_duration_ms = elapsed - paused_duration_ms), sets Session.status=completed, emits completion event. Break is explicit: frontend sends /api/session/start-break after receiving completion event; backend creates new Session with status=idle (or status=running if auto-starting break). Indexing on Session.started_at, SessionRecord.completed_at. Invariants: (1) session has exactly one active record (status != completed) at any time; (2) SessionRecord written only when status transitions to completed; (3) paused_duration_ms always >= 0 and monotonically increasing.

**Resolution:**

Integrated with Tweedledee's session-state-machine and session-completion-event contracts. Full Feature-001 session lifecycle settled: backend enforces state transitions at schema level, validates before write, atomically appends SessionRecord and updates Session.status on completion, emits completion event only after atomic write succeeds. Frontend subscribes to Session state changes, reconciles local timer with server duration on every update, displays break countdown and explicit break-start request. No implicit session state; no dangling incomplete sessions. Ready for test scenarios.
