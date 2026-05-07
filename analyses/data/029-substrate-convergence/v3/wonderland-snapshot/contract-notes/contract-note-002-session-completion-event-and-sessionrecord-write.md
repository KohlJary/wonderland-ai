## Contract Note 002: Session completion event and SessionRecord write

**State:** agreed
**Contract Version:** v1 (SessionRecord atomic write on completion: (1) calculate final session_duration_ms and break_duration_ms from timestamps, (2) write SessionRecord row in same transaction, (3) set Session.status=completed; completion event fires only after all three succeed; frontend does NOT increment break auto-create; explicit start-break request with idempotency key required)

**Current Shape:**

no prior agreement

**Proposed Change:**

When a session reaches completion (countdown hits zero or user explicitly completes), backend: (1) calculates final session_duration and break_duration from timestamps, (2) writes a single record to SessionRecord atomically with Session.status = completed, (3) sends a completion event to frontend. Frontend receives the completion event, plays a notification sound (if enabled), displays break countdown UI, and then sends a start-break request to backend to begin the next session state.

**Source:** Feature 001 (session→break transition), ADR-001 (Timer→History atomic write)

**Frontend Impact (Tweedledee):**

Frontend displays a 'session complete' UI state briefly (1-2s animation), then transitions to break timer view. Frontend must handle the case where the completion event arrives but the WebSocket disconnects before the frontend sends start-break request — in that case, when the socket reconnects, frontend polls the current session state and resumes from there (could be in-break, could be completed-waiting-for-user). No client-side session state persists across app restarts (that's the backend's job); frontend only holds transient timer display.

**Backend Impact (Tweedledum):**

Completion is atomic: (1) calculate final session_duration_ms and break_duration_ms from timestamps (started_at, completed_at, paused_duration_ms), (2) write SessionRecord row in same transaction, (3) set Session.status=completed. Only after all three succeed does the completion event fire to frontend. If SessionRecord write fails, the transaction rolls back and frontend does not receive completion event — client is left in running state and can retry. On recovery (client reconnects), polling current session state returns 'running', frontend continues timer. Break start is explicit: frontend sends start-break request only after receiving completion event and user sees 'break' UI. Backend creates a new Session row with status=running and session_type=break when break-start request arrives. Idempotency key (request_id) on start-break prevents duplicate break sessions if frontend retries.

**Resolution:**

Integrated with Note 001 (state machine) and Note 003 (full Feature 001). Atomicity is clear: no SessionRecord is written unless all three steps succeed (duration calculation + write + status update). Completion event is the signal to frontend that SessionRecord was successfully persisted. Break is explicit (no auto-creation): frontend sends start-break request as a separate action after showing break UI. Idempotency key on start-break prevents duplicate sessions if the request retries. Both sides agree on the seam: backend guarantees atomic persistence, frontend guarantees explicit user-initiated break creation.
