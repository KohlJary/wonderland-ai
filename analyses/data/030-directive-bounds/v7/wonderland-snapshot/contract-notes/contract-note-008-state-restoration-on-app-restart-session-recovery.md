## Contract Note 008: State restoration on app restart (session recovery)

**State:** agreed
**Contract Version:** v1 (session-recovery-on-restart)

**Current Shape:**

GET /session/current endpoint returns in-flight session state on app startup: if a session was in progress when the app exited, return { phase, elapsed_seconds, session_length_sec, break_length_sec, session_id, started_at }. If no in-flight session, return { status: 'idle' }. Frontend can resume from that point without losing context.

**Agreed Changes:**

Session recovery via GET /session/current endpoint as proposed. Frontend owns timer authority during background execution (Option B from the proposal: client times locally, backend is stateless on in-flight sessions).

**Frontend Impact (Tweedledee):**

On app startup: (1) check localStorage for in-flight session (populated when a session transitions to a new phase or is completed). (2) If localStorage has a recent session (timestamp within last 24 hours), resume from there with local timer continuing from where it left off. (3) If localStorage is empty or stale (> 24 hours old), call GET /session/current to check backend for recovery state. (4) If backend returns idle state, show home screen with "Start Session" button. (5) If backend returns an in-flight session (unexpected, shouldn't happen if frontend properly recorded completion), accept it and resume.

Timer accuracy: Frontend drives the timer locally using wall-clock time (Date.now()). When resuming after app restart, I calculate elapsed_seconds as (now - session_start_time), which accounts for the time the app was closed. This assumes device clock is reasonably accurate. If device clock has drifted (e.g., user changed it), elapsed_seconds could be off by minutes; this is acceptable for a personal productivity app.

localStorage persistence: I persist session state after every phase transition (when a session moves from focus to break, or break to idle). This ensures recovery can happen even if the app crashes during a transition.

**Backend Impact (Tweedledum):**

Backend provides GET /session/current endpoint: returns empty state { status: 'idle' } if no persisted in-flight session, or returns the last-known session metadata (for audit/recovery purposes, not for timing). Backend does not track elapsed_seconds for in-flight sessions — that's entirely frontend responsibility. Backend only records immutable session-completion facts via POST /sessions/complete.

In-flight sessions are not persisted in the database (they live in frontend localStorage only). The backend's /session/current endpoint is a safety valve: if frontend localStorage is corrupted or missing, this endpoint can tell the frontend "no session in progress, you're safe to start a new one."

**Agreed By:** Tweedledee and Tweedledum (resolved in test-scenarios thread)
**Date:** M4, test-scenarios

**Notes:**

Clock drift risk: if a user's device clock is adjusted during app shutdown, the elapsed time could be wrong when the app resumes. Example: app closes at 3pm with 10 min remaining in a 25-min session; user resets their clock to 1pm; app reopens and calculates elapsed = 2 hours (completely wrong). This is a known limitation. If billing or other critical functions depend on exact session duration, this needs reconsideration. For personal productivity tracking, this is acceptable.

Concurrent sessions: frontend ensures only one session can be in-flight at a time. If a user has the app open in two tabs, both tabs share localStorage (on same device). The second tab to POST /sessions/complete wins; the first tab's in-flight session is abandoned. This is acceptable (users shouldn't have the app open in two tabs simultaneously).

GET /session/current behavior: returns idle state if no persisted session, not an error. Frontend calls this endpoint after app restart to double-check if there's a recovery session; if there isn't, frontend proceeds to home screen. This is a defensive check, not a normal path.
