## Test Scenario 005: Adjust session and break lengths — configuration correctness

**Source:** feature-005-adjust-session-and-break-lengths
**Persona:** Sam, 42, a writer
**Severity:** high (usability depends on config being applied correctly)
**Concern:** Config validation, persistence, and application to new sessions

---

## Happy Path

**Scenario: Sam customizes her pomodoro rhythm**

1. Sam opens settings
2. She sees current defaults: "Session: 25 min | Break: 5 min"
3. She taps on session duration and changes it to 50 minutes
4. She taps on break duration and changes it to 10 minutes
5. She taps "Save" (or changes auto-save)
6. She returns to the main screen
7. She starts a new session — the timer counts down from 50 minutes
8. **Observable outcome:** Her custom defaults persist and are used for all future sessions

---

## Failure Modes

**Hatter's Breakdown:**

1. **Out-of-range validation bypassed** — Sam sets session length to 0 or 500 minutes
   - **Why this matters:** Timer would be meaningless (instant or unrealistic)
   - **Severity:** high (breakage)

2. **Partial update resets unmentioned fields** — Sam updates session length, break length reverts to default
   - **Why this matters:** User's customization is silently lost
   - **Severity:** high (silent wrongness)

3. **Type coercion failure** — client sends "50" (string) instead of 50 (number)
   - **Why this matters:** Backend might crash or ignore the request
   - **Severity:** medium (depends on error handling)

4. **Active session ignores new config** — Sam changes session length mid-session, timer is affected
   - **Why this matters:** User expects current session to keep original duration; only next session uses new default
   - **Severity:** medium (violates principle of immutability for running sessions)

5. **Config not persisted across requests** — Sam sets config, refreshes page, config resets to default
   - **Why this matters:** User's customization is lost; feature is useless
   - **Severity:** high (feature failure)

6. **Concurrent config updates race** — two simultaneous PATCH requests; one change is lost
   - **Why this matters:** One setting silently overwrites the other
   - **Severity:** low (rare, but possible)

7. **Response includes stale data** — PATCH /config returns the old values instead of new ones
   - **Why this matters:** Frontend shows user the wrong values, assuming update succeeded
   - **Severity:** medium (UX confusion)

8. **Timezone not included in response** — GET /config doesn't return timezone field
   - **Why this matters:** Frontend can't display/edit timezone; feature is incomplete
   - **Severity:** low (nice-to-have for v1)

9. **Seconds conversion wrong** — config says 50 min, but session starts with 2500 seconds (not 3000)
   - **Why this matters:** Timer runs wrong duration
   - **Severity:** high (breakage)

10. **Config endpoint requires auth (not yet tested)** — GET/PATCH /config works without auth in test
    - **Why this matters:** Security issue when multi-user is added; test now to avoid regression
    - **Severity:** low (future concern)

---

## Test Implementation

See `tests/test_session_005_config.py`:

- **Happy path:** `TestSessionConfigHappyPath` — Sam fetches, updates, sees it applied
- **Edge cases:** `TestSessionConfigEdgeCases` — validation, persistence, concurrency, etc.

**Red-green target:** All tests in `test_session_005_config.py` should fail until M5 implements:
- GET /config endpoint
- PATCH /config endpoint
- Validation: session_length_minutes in [1, 120], break_length_minutes in [1, 60]
- Proper config persistence (local or DB, doesn't matter for v1)
- Config applied to new sessions (target_duration_seconds = config * 60)
- Partial updates don't reset unmentioned fields
