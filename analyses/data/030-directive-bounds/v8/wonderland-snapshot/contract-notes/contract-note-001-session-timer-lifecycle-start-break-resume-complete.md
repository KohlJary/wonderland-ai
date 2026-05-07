## Contract Note 001: Session timer lifecycle: start, break, resume, complete

**State:** proposed_backend_response
**Contract Version:** v1 (proposed)

**Current Shape:**

no existing shape; this is the v1 seam between frontend timer UI and backend session persistence

**Proposed Change:**

Define the session lifecycle events and state shape. Frontend sends 'start-session' with optional custom durations (focus_minutes, break_minutes; defaults 25, 5). Backend creates a transient current_session in memory tracking elapsed_time, phase (focus|break), and state (running|paused|completed). Backend emits events: session-started, break-started, session-completed. Frontend reads current state via polling or WebSocket subscription and updates UI.

**Source:** Feature 001: Run a focus session with breaks (stories 001, 002)

**Frontend Impact (Tweedledee):**

Frontend receives 'start-session' from user (with optional durations), sends to backend, then polls or subscribes to current_session state. UI renders phase (focus|break), remaining time (elapsed_time subtracted from phase duration), and state (running|paused|completed). On session-completed event, persist to local history and reset UI to idle. 

Two state machines: (1) local timer ticking for UI feedback (smoother than polling), reconciled against backend phase when state arrives, (2) phase state received from backend (source of truth). Failure mode: clock skew between client timer and backend elapsed_time — frontend shows 3 seconds left but break already started on server. Handling: on next state event from backend, jump to correct phase (no animation, just truth). 

Client state: one transient current_session in memory (phase, elapsed_time, local_end_time for timer tick). No persistence between requests — stateless component re-reads from backend on every subscription or poll.

**Backend Impact (Tweedledum):**

Backend maintains transient in-memory current_session per session_id (see CN-003 for session_id scoping). 

**Endpoints:**
- `POST /api/sessions/start` — accepts {focus_minutes?, break_minutes?}, validates durations (1–999 minutes), creates current_session in memory with state=running, phase=focus, elapsed_time=0, returns {session_id, state, phase, elapsed_time, focus_duration, break_duration}.
- `GET /api/sessions/current` — returns current session state {phase, state, elapsed_time, focus_duration, break_duration}; 404 if no active session.
- `POST /api/sessions/current/pause` — transitions state from running → paused; returns updated state; 409 if already paused.
- `POST /api/sessions/current/resume` — transitions state from paused → running; returns updated state; 409 if already running.
- `POST /api/sessions/current/complete` — marks session completed, persists to sessions table with started_at/completed_at/phase_sequence, clears transient state, returns final state; 409 if already completed.

**Timer mechanism:** Backend runs a background task (one per running session or a shared tick loop) that increments elapsed_time every 1 second. When elapsed_time reaches focus_duration (in minutes, converted to seconds), automatically transition to break phase (emit event, set elapsed_time=0, phase=break). When elapsed_time reaches break_duration, automatically mark complete (emit session-completed, persist to DB, clear transient).

**State invariants enforced:**
- A session can only be running, paused, or completed; never multiple states simultaneously.
- Elapsed time is never negative and never exceeds the current phase duration.
- Only one current_session per session_id; creating a new session when one is active clears the old (no queuing).
- Transient state is lost on backend restart; no recovery from database for in-flight sessions.

**Failure modes handled:**
- If backend crashes mid-session: on next GET /api/sessions/current, 404 (session lost). Frontend detects 404 and shows "session expired" message. User must start new session.
- If pause request arrives but session already paused: return 409 with message "session already paused."
- If complete request arrives but timer hasn't fired: return 409 with message "timer still running."

**Polling vs. WebSocket:** For v1, implement polling endpoint (GET /api/sessions/current returns current state). Frontend polls every 1s. WebSocket is stretch goal; don't build it now.

**Clock source:** Use server time for elapsed_time. Never trust client clock.

**Open question for Tweedledee:** When elapsed_time reaches a phase duration and we auto-transition, do you want an event response (e.g., session state changes from focus to break) or just a state change visible on the next poll? Current assumption: state change is visible on next poll; no explicit event broadcast. If you need immediate notification, we shift to WebSocket or server-sent events. Which?

**Concern:** The proposal mentions "backend emits events: session-started, break-started, session-completed" but doesn't specify the mechanism (WebSocket, Server-Sent Events, polling discovery). I'm proposing polling discovery (client sees state change on next GET /api/sessions/current, infers the event). If that's not acceptable, we need to add WebSocket support, which changes the scope significantly. Confirm intent.

**Ready to mark agreed:** once the polling vs. WebSocket and event delivery questions are answered.
