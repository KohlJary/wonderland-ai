## Scenario 002: Marcus manually completes session early (10 min instead of 25)

**Severity:** degradation

**Setup:**

Marcus started session 10 minutes ago. Timer running. Session in database with started_at.

**Trigger:**

Marcus taps 'Mark Done' early. Frontend POSTs /complete with completed_at = started_at + 600 seconds.

**Expected:**

Backend accepts (completed_at within valid range). Session persists with 10-minute actual duration.

**Concern:**

Backend might reject early completion, forcing users to wait. This breaks user agency.

**Property:**

All completed_at ∈ [started_at, started_at+duration_seconds+jitter] are accepted.

**Implies:**
- Test file: tests/test_sessions_lifecycle.py
