## Test Scenario 002: Invalid session duration rejected (Feature 001)

**Feature:** Run a focus session with breaks
**Severity:** high

**Scenario:**

A client sends a start-session request with focus_minutes=0 or focus_minutes=-5 or focus_minutes=9999. The backend rejects the request with a clear error (400 Bad Request + validation message).

**What breaks if this fails:**

The state machine can be poisoned by invalid durations, leading to timers that never fire, or UI states that hang. Validation at the boundary prevents this.

**Acceptance Criteria:**

- POST /api/sessions/start with focus_minutes <= 0 returns 400 with error_code "invalid_duration"
- POST /api/sessions/start with focus_minutes > 999 returns 400 with error_code "invalid_duration"
- POST /api/sessions/start with break_minutes <= 0 returns 400 with error_code "invalid_duration"
- Valid range for both: 1–999 minutes (inclusive)
- Error response includes a human-readable message, e.g., "focus_minutes must be between 1 and 999"
