## Scenario 018: User updates only session duration (break duration unchanged)

**Severity:** degradation

**Setup:**

Current settings: session=1500, break=300.

**Trigger:**

Frontend PUTs /api/settings with {session_duration_seconds: 2400} (omitting break).

**Expected:**

Backend accepts partial update. Returns {session_duration_seconds: 2400, break_duration_seconds: 300}.

**Concern:**

Endpoint should support partial updates.

**Property:**

PUT /settings accepts partial payloads. Omitted fields retain previous values.

**Implies:**
- Test file: tests/test_settings.py
