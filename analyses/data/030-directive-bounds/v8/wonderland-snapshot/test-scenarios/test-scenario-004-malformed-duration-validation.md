## Test Scenario: Malformed duration (negative, zero, or non-integer) in start-session request should reject

**Severity:** breakage

**Feature:** Feature 001: Run a focus session with breaks

**Setup:**

Frontend user (or malicious client) calls POST /sessions with {session_id, focus_minutes: -5, break_minutes: 0}.

**Trigger:**

Backend receives request with invalid durations.

**Expected:**

Backend validates and rejects with 400 Bad Request {error: 'focus_minutes must be positive integer'}. current_session is NOT created.

**Concern:**

If validation is missing, backend accepts negative minutes. Timer logic with elapsed_time >= -5 immediately fires. Or zero minutes creates a timer that never runs. User experience breaks: timer either instant-fires or never fires.

**Property:**

For all start-session requests R, if focus_minutes < 1 or break_minutes < 1, backend rejects with 400.

**Implications:**

None noted.
