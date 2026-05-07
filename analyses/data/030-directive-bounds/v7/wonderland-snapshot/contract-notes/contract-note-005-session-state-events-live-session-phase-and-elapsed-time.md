## Contract Note 005: Real-time session state events (phase transitions)

**State:** agreed_with_clarification
**Contract Version:** v1 (websocket-phase-transitions)

**Current Shape:**

Define the event envelope for real-time session state updates: includes phase (focus|break|idle), elapsed_seconds in current phase, total_session_count today, settings applied (session_length_sec, break_length_sec). Frontend needs: (1) initial state on session start, (2) phase-transition events (focus→break, break→focus, session→idle).

**Agreed Changes:**

Use WebSocket for phase-transition events (not per-second polling). Frontend-driven timer with backend phase-transition signaling.

On session start (POST /sessions/start): Backend returns initial { phase, elapsed_seconds, total_session_count, session_length_sec, break_length_sec }.

Frontend then drives local setInterval timer; backend only sends *phase-transition* events when a phase ends (focus duration expires → send break-start event; break duration expires → send focus-ready or session-end event).

Event envelope on phase transition: { phase ('focus'|'break'|'idle'), elapsed_seconds_at_transition (server's authoritative count), total_session_count (updated), timestamp_iso8601 }.

**Frontend Impact (Tweedledee):**

On session start, I receive initial state envelope from POST /sessions/start. I then drive a local setInterval timer (tick every 100ms for smooth countdown display). I listen for WebSocket phase-transition events; when a transition fires, I update the local state immediately (phase, elapsed_seconds, total_session_count) and present the next UI state (e.g., "Session Complete! Take a break?").

If WebSocket disconnects during an active session, I continue running the local timer (best-effort) until reconnection. On reconnect, I re-fetch GET /session/current to resync elapsed_seconds and phase (in case the phase transitioned while offline). This handles the case where the user was away during the transition and the local timer drifted.

**Backend Impact (Tweedledum):**

Backend accepts WebSocket subscriptions from authenticated users. On POST /sessions/start, backend returns initial state envelope. During an in-flight session, backend calculates phase-transition moments (when elapsed_seconds >= focus_duration_seconds, transition to break; when elapsed_seconds >= focus_duration_seconds + break_duration_seconds, transition to idle). At each transition, backend sends a phase-transition event to the connected WebSocket client (or broadcasts to all open sessions for this user if they have multiple tabs).

Backend does not send per-second tick events. Backend is authoritative on phase transitions and elapsed_seconds (backend timestamp is the truth; frontend's local timer is for display continuity, not accuracy).

On GET /session/current: backend returns the current in-flight session state, or { status: 'idle' } if no session in progress. This endpoint is used on app restart (frontend checks localStorage first, then calls GET /session/current if localStorage is empty or stale).

**Agreed By:** Tweedledee and Tweedledum (resolved in test-scenarios thread)
**Date:** M4, test-scenarios

**Notes:**

Polling alternative explicitly rejected: per-second polling would create latency on phase transitions and waste bandwidth. WebSocket is the right choice for this UX requirement.

Offline handling: if device goes offline during a session, frontend continues the local timer; on reconnect, frontend resyncs from server. This ensures the UX doesn't stall, and accuracy recovers when connectivity returns.

Reconnection edge case: if the user's local timer has drifted significantly during offline time, GET /session/current on reconnect will show the server's authoritative elapsed_seconds, and frontend will correct the display. This is acceptable.
