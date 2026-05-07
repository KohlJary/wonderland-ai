## Test Scenario 002: Marcus completes session early (manual 'done' button)

**Severity:** degradation

**Setup:**
Marcus started a session 10 minutes ago. Timer is still running. Session_id and started_at are in database.

**Trigger:**
Marcus taps 'Mark Session Done' early. Frontend POSTs /api/sessions/{id}/complete with completed_at = started_at + 600 seconds.

**Expected:**
Backend accepts (completed_at is within valid range). Session persists with actual_duration=10 minutes. GET /api/sessions/{id} returns session with completed_at timestamp reflecting the early completion.

**Concern:**
Backend might enforce completed_at ≥ started_at + duration_seconds, rejecting early completion. This breaks user control over session lifecycle. Test verifies early exit is allowed.

**Property:**
For all completed_at where started_at < completed_at ≤ started_at + duration_seconds + jitter, the session is persisted successfully.

**Implies:**
- Feature 001 (user can end session early)
- Test file: tests/test_sessions_lifecycle.py
