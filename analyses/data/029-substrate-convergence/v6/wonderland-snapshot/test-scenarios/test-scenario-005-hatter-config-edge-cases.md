## Test Scenario: Session Configuration Edge Cases

**Severity:** breakage, silent-wrongness, degradation

**Setup:**

Sam has customized her session/break lengths. She now adjusts them repeatedly, patches only some fields, and tests boundary conditions. The system must validate inputs, persist state, and apply new defaults to future sessions without affecting active or completed sessions.

**Trigger:**

Sam makes successive config changes:
1. PATCH /config with session_length_minutes=50 (valid)
2. PATCH /config with session_length_minutes=0 (invalid)
3. PATCH /config with session_length_minutes=-10 (invalid)
4. PATCH /config with session_length_minutes=121 (out of range)
5. PATCH /config with only session_length_minutes (leaving break_length_minutes unchanged)
6. GET /config after partial patch (should preserve omitted field)

**Expected:**

1. Valid update (50) returns 200 OK with new config
2. Zero-length returns 400 Bad Request with clear error
3. Negative length returns 400 Bad Request
4. Out-of-range (>120 min) returns 400 Bad Request; acceptable range is 1–120 minutes
5. Partial PATCH preserves previous break_length_minutes value
6. GET /config returns the current config including unmodified fields

**Concern:**

Breakage:
- Invalid config is accepted, leading to zero-duration or infinite sessions
- PATCH succeeds but GET returns different values (persistence fails silently)
- Config change affects already-running session (should only affect next session start)

Silent-wrongness:
- Partial PATCH resets omitted fields to default (Sam's break length reverts to 5 when she patches session length)
- Config is cached globally; one user's change affects all users
- Fractional minutes (25.5) are accepted but truncated to 25 (user thinks they set 25.5)
- Type coercion: "50" (string) is coerced to 50, masking API contract violation

Degradation:
- Out-of-range input causes 500 error instead of clear 400
- No clear error message indicating valid range (user doesn't know if 121 is too high)
- Config change requires app restart to take effect (should be immediate)
- Concurrent PATCHes race; one change is lost

**Property:**

For all users U and config values V:
- PATCH /config with valid V returns 200 OK and persists V
- Subsequent GET /config returns V
- If PATCH includes only some fields, omitted fields retain previous values
- V values must be positive integers in range 1–120 (session) and 1–60 (break)
- For all sessions S started by U after PATCH, S.target_duration = V.session_length * 60

**Implies:**

- Implies input validation with clear error messages
- Implies atomic/transactional PATCH (all-or-nothing, no partial updates)
- Implies per-user config storage (not global shared state)
- Implies config defaults: session_length_minutes=25, break_length_minutes=5, timezone="UTC"
