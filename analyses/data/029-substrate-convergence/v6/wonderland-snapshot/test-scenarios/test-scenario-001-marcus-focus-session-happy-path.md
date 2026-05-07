## Test Scenario: Marcus Starts and Completes a Focus Session

**Severity:** breakage (if this fails, the core feature is broken)

**Setup:**

Marcus is a 28-year-old software engineer with ADHD. He's sitting at his desk with a task to focus on. The app is fresh (no active sessions). The system has the default 25-minute session configuration.

**Trigger:**

Marcus taps "Start Session" in the app. The button completes the request and he sees the timer begin counting down from 25:00. The app is minimized. After 25 minutes expire (simulated in test), Marcus sees a notification that the session is complete.

**Expected:**

1. The start request returns immediately with HTTP 201 Created
2. The response includes the session ID, start time (server-provided), target duration (1500 seconds), and current elapsed time (should be ~0)
3. The session can be fetched to verify it's active
4. When the timer expires, Marcus can call POST /sessions/{id}/complete
5. The complete request returns HTTP 200 with end_time, duration_seconds, and is_completed=true
6. The completed session appears in GET /sessions/today
7. The today summary shows count=1

**Concern:**

The happy path is straightforward, but the concern is that implementation might:
- Not provide server-side timing (client clock drift issues)
- Fail on concurrent start requests (Marcus accidentally taps twice)
- Return malformed responses that the frontend can't parse
- Fail to persist the session to the database

**Property:**

For all users U and focus sessions S started by U:
- POST /sessions/start returns S with is_active=true and target_duration > 0
- POST /sessions/{S.id}/complete transitions S to is_completed=true, is_active=false
- S appears in GET /sessions/today with S.is_completed=true

**Implies:**

- Implies backend Session model and API endpoints /sessions/start and /sessions/{id}/complete
- Implies database schema for sessions (id, user_id, start_time, end_time, target_duration_seconds, is_active, is_completed, created_at, updated_at)
- Implies server-side timestamp generation (no client-provided times)
