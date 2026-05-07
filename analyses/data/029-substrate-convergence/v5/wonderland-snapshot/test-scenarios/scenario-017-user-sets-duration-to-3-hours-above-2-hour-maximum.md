## Scenario 017: User sets duration to 3 hours (above 2-hour maximum)

**Severity:** degradation

**Setup:**

User in settings, inputs 10800 seconds (3 hours).

**Trigger:**

Frontend PUTs /api/settings with {session_duration_seconds: 10800}.

**Expected:**

Backend rejects with 400/422. Error mentions maximum.

**Concern:**

Bounds enforcement prevents absurd session durations.

**Property:**

PUT /settings with duration_seconds > 7200 returns 400/422.

**Implies:**
- Test file: tests/test_settings.py
