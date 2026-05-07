## Scenario 019: Settings persisted across app restarts

**Severity:** degradation

**Setup:**

User set session duration to 2400 seconds and closed app.

**Trigger:**

App restarts. Frontend GETs /api/settings on app launch.

**Expected:**

Backend returns {session_duration_seconds: 2400}. Settings are persistent.

**Concern:**

Settings must persist on backend across app restarts.

**Property:**

GET /settings returns the most recent settings saved via PUT /settings.

**Implies:**
- Test file: tests/test_settings.py
