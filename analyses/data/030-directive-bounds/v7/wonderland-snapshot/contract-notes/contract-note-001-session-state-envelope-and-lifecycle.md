## Contract Note 001: Session state envelope and lifecycle

**State:** agreed
**Contract Version:** v1 (session-state-envelope)

**Current Shape:**

Frontend receives and displays session state as: { session_id (UUID), phase ('focus'|'break'|'idle'), session_start_time (ISO8601), focus_duration_seconds (int), break_duration_seconds (int), elapsed_seconds (int), time_remaining_seconds (int), completed_sessions_today (int) }.

**Agreed Changes:**

Session state envelope and lifecycle as proposed. Frontend holds session state in memory and persists to localStorage on every phase transition. Frontend drives the timer locally (setInterval-based countdown) — backend does not tick the timer. Frontend receives this envelope on session start (POST /sessions/start response) and persists it across app restarts.

**Frontend Impact (Tweedledee):**

Frontend holds session state in memory: { session_id, phase ('focus'|'break'|'idle'), session_start_time, focus_duration_seconds, break_duration_seconds, elapsed_seconds, time_remaining_seconds, completed_sessions_today }. Frontend drives the timer locally (setInterval-based countdown) — backend does not tick the timer. I'll persist this state to localStorage on every phase transition so recovery is possible on app restart (Feature-002). Frontend optimistically updates phase and elapsed_seconds; backend receives immutable completion events only.

**Backend Impact (Tweedledum):**

Backend returns session state envelope on POST /sessions/start (session initialized response). Backend does not send per-tick updates. Backend does not track elapsed_seconds during in-flight sessions — elapsed_seconds is calculated by frontend. Backend only receives immutable session completion events via POST /sessions/complete. Phase transitions are determined by backend completion logic (at what point does a session "expire"?), but backend does not send tick events — frontend determines when timer reaches 0:00 and POSTs completion event.

**Agreed By:** Tweedledee and Tweedledum (resolved in test-scenarios thread)
**Date:** M4, test-scenarios

**Notes:**

Frontend time authority: frontend owns the timer display. Backend owns the session facts (completed_at timestamp is the source of truth for accounting). This contract assumes device clock is reasonably accurate; if device clock drifts during app shutdown, elapsed_seconds on restart may be off by minutes. This is acceptable for personal productivity (not a billing system).
