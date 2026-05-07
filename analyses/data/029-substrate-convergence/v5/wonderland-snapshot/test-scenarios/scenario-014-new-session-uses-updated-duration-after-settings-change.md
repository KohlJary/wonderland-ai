## Scenario 014: New session uses updated duration after settings change

**Severity:** breakage

**Setup:**

User just changed settings to 1800 seconds. Frontend caches new settings.

**Trigger:**

User starts new session. Frontend POSTs /sessions/start with {duration_seconds: 1800}.

**Expected:**

Session persists with duration_seconds=1800. GET /sessions/{id} shows 1800.

**Concern:**

Frontend must pass duration in request body, not rely on backend query.

**Property:**

Sessions created after PUT /settings have duration matching new settings.

**Implies:**
- Test file: tests/test_settings.py
