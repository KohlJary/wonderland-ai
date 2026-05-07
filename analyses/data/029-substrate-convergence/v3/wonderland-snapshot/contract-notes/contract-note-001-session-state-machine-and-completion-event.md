## Contract Note 001: Session state machine and completion event

**State:** agreed
**Contract Version:** v1 (Session state machine enforced at schema level: new→running→paused→completed; state transitions validated before write; frontend reconciles transient timer on state update; clock drift >1s triggers hard reset; Session snapshot includes started_at, paused_duration_ms, completed_at for duration calculation)

**Current Shape:**

no prior agreement

**Proposed Change:**

Session entity represents current or in-progress session (per ADR). State machine: new → running → (paused|completed). On completion: backend atomically writes completed session to SessionRecord. Frontend subscribes to session state changes (WebSocket or polling) and emits UI updates based on running|paused|completed status.

**Source:** Feature 001 (Run focused session with break), ADR-001 (Session entity design)

**Frontend Impact (Tweedledee):**

Frontend manages the visual timer (decrementing countdown display, state-driven UI — showing 'running' vs 'paused' vs 'break countdown'). Frontend emits start-session and pause-session requests to backend. Frontend receives session state updates and renders them. Client holds the *transient timer display* (the user sees X:XX) but not the canonical session duration — that comes from the backend's session_length field. Frontend reconciles its local ticker with server state on every state update (reset local counter if server duration differs by >1s, which catches clock drift or backend-driven pause).

**Backend Impact (Tweedledum):**

Session table enforces state machine at the schema level: status enum [new|running|paused|completed]. State transitions validated in application code before database write — new→running requires Session.started_at to be null (prevents duplicate starts); running→paused requires started_at != null; paused→running allowed if paused_duration_ms is updated; running→completed and paused→completed both atomically write to SessionRecord in same transaction. No dangling incomplete sessions. Frontend reconciliation on state update (reset local timer if server duration differs >1s) keeps display in sync with source of truth on backend.

**Resolution:**

Integrated with Contract Note 002 (completion event) and Note 003 (full Feature 001 lifecycle). Backend state validation is clear: idempotent transitions, atomic SessionRecord write on completion, no implicit state changes. Frontend timer display is minimalist and resilient to clock drift. Both sides agree: canonical session state lives on backend; frontend displays it transiently and reconciles on every server message.
