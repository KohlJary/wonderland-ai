## Test Scenario 001: Focus session happy path (Feature 001)

**Feature:** Run a focus session with breaks
**Persona:** Marcus, software engineer protecting deep work time
**Severity:** critical

**Scenario:**

Marcus opens the app and taps "Start 25-minute session." The backend creates a new session record with state=running, phase=focus, elapsed_time=0, focus_duration=25 (minutes). The backend emits a session-started event. Marcus watches the timer count down for 25 minutes. At exactly 25 minutes elapsed, the backend transitions phase from focus to break, emits a break-started event, and resets elapsed_time to 0 with break_duration=5. Marcus receives a notification that the break has started. After 5 minutes, the backend emits session-completed, writes the full session record to the database, and resets the transient state. Marcus can see the session in history.

**What breaks if this fails:**

The core loop of the app — start, work, break, rest. Without this, nothing else works.

**Acceptance Criteria:**

- POST /api/sessions/start returns 200 with {session_id: uuid, state: "running", phase: "focus", elapsed_time: 0, focus_duration: 25, break_duration: 5}
- GET /api/sessions/current returns current state every second (or via WebSocket subscription)
- At elapsed_time == focus_duration, backend auto-transitions: phase becomes "break", elapsed_time resets to 0
- At elapsed_time == break_duration, backend auto-transitions: state becomes "completed"
- Session written to database has all fields: session_id, user_session_id, phase_sequence (focus→break→complete), total_focus_duration, total_break_duration, started_at, completed_at, created_at

**Concern:**

The contract specifies in-memory transient state + database write on completion. The test assumes the backend has a timer mechanism (setInterval or equivalent) running continuously. If the backend uses polling or event-driven timers instead, the "at exactly N seconds" assertion becomes looser. This should be clear in implementation.
