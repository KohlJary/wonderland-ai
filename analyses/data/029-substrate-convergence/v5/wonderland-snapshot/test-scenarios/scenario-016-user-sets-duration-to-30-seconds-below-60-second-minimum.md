## Scenario 016: User sets duration to 30 seconds (below 60-second minimum)

**Severity:** degradation

**Setup:**

User in settings, inputs 30 seconds.

**Trigger:**

Frontend PUTs /api/settings with {session_duration_seconds: 30}.

**Expected:**

Backend rejects with 400 or 422. Error message mentions minimum. Settings NOT updated.

**Concern:**

Error message must be clear for frontend to show helpful user feedback.

**Property:**

PUT /settings with duration_seconds < 60 returns 400/422 with descriptive error.

**Implies:**
- Test file: tests/test_settings.py
