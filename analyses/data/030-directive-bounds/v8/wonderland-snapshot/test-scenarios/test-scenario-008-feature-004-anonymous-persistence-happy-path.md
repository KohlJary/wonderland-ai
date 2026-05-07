## Test Scenario 008: Anonymous persistence happy path (Feature 004)

**Feature:** Use the app without sign-up
**Persona:** Devon, casual timer user, opens app on first visit
**Severity:** critical

**Scenario:**

Devon visits the app for the first time. The frontend generates a UUID session_id and stores it in localStorage. Devon starts a session (25/5 pomodoro). The backend receives the request with session_id in the header (or query param). The session is completed and written to the database, scoped by session_id. Devon closes the app. The next day, Devon reopens the app. The frontend retrieves session_id from localStorage (same UUID). The backend loads that session_id's data. GET /api/sessions returns Devon's one completed session from yesterday. No sign-in, no friction, data is there.

**What breaks if this fails:**

The core value prop of the app (instant use, no friction) is lost. Users have to sign in or lose their history.

**Acceptance Criteria:**

- First request to backend includes X-Session-ID header (or session_id query param) with UUID
- Backend creates sessions/settings rows scoped to session_id
- Completed session written to database is retrievable via GET /api/sessions with same session_id
- localStorage session_id persists across browser close/reopen (frontend responsibility, but backend must support)
- Second request with same session_id returns data from first request (no duplicate sessions, correct partition)
- Backend auto-creates settings row on first request (default 25/5) if none exists for session_id
