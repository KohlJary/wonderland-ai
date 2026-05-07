## Test Scenario 001: Marcus starts a 25-minute session and receives completion feedback

**Severity:** breakage

**Setup:**
Marcus is at the app's main screen, settings default to 25 minutes (1500 seconds). Backend is running. Time is afternoon UTC.

**Trigger:**
Marcus taps 'Start Session'. Frontend POSTs /api/sessions/start with {duration_seconds: 1500}. Frontend simulates 1500 seconds elapsing via local timer. Frontend POSTs /api/sessions/{session_id}/complete with {completed_at: <now>}.

**Expected:**
Backend returns 202 on /sessions/start with {session_id, started_at}. Backend accepts /sessions/{session_id}/complete, validates timing (completed_at within [started_at, started_at+1500+jitter]), persists session record. Returns 200 with full session record. Session is queryable via GET /api/sessions/today.

**Concern:**
Backend may reject /complete if started_at → completed_at timing doesn't match contract expectations. Jitter buffer width is critical: if too tight, normal clock skew causes rejections; if too loose, sessions recorded with wildly inaccurate timestamps.

**Property:**
For all /sessions/{id}/complete calls where completed_at ∈ [started_at, started_at+duration_seconds+jitter], backend persists and returns 200.

**Implies:**
- Test file: tests/test_sessions_lifecycle.py
