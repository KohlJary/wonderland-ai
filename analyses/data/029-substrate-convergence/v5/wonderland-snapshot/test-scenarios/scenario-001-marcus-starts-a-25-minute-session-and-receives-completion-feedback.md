## Scenario 001: Marcus starts a 25-minute session and receives completion feedback

**Severity:** breakage

**Setup:**

Marcus is at the app's main screen, settings default to 25 minutes (1500 seconds). Backend is running.

**Trigger:**

Marcus taps 'Start Session'. Frontend POSTs /api/sessions/start with {duration_seconds: 1500}. Frontend simulates timer expiry (1500 seconds). Frontend POSTs /api/sessions/{session_id}/complete with {completed_at: <now>}.

**Expected:**

Backend returns 202 with {session_id, started_at}. Backend accepts /complete, validates timing, persists session. Returns 200 with full record. Session queryable via GET /api/sessions/today.

**Concern:**

Jitter buffer width is critical—if too tight, clock skew causes rejections; if too loose, durations are inaccurate. Contract does not specify exact jitter; implementation must choose robustly.

**Property:**

For all /sessions/{id}/complete where completed_at ∈ [started_at, started_at+duration_seconds+jitter], backend persists and returns 200.

**Implies:**
- Test file: tests/test_sessions_lifecycle.py
