## Scenario 013: User customizes session duration from 25 to 30 minutes

**Severity:** breakage

**Setup:**

User in settings view. Current: session_duration_seconds=1500, break_duration_seconds=300.

**Trigger:**

User enters 30 (minutes). Frontend PUTs /api/settings with {session_duration_seconds: 1800}.

**Expected:**

Backend validates (1800 ∈ [60, 7200]), writes settings, returns 200 with {session_duration_seconds: 1800, break_duration_seconds: 300, settings_updated_at}.

**Concern:**

Backend must enforce [60, 7200] bounds per contract.

**Property:**

PUT /settings validates all duration fields. Accepts only ∈ [60, 7200] seconds.

**Implies:**
- Test file: tests/test_settings.py
