## Scenario 008: Devon views completed session count for today

**Severity:** breakage

**Setup:**

Devon completed 4 sessions today (started_at within UTC midnight boundaries).

**Trigger:**

Frontend GETs /api/sessions/today.

**Expected:**

Backend returns array of 4 session records. Frontend renders '4 sessions completed today'.

**Concern:**

Definition of 'today': contract says frontend normalizes local midnight, backend filters UTC. If user in PST, 11 PM PST = 7 AM UTC next day.

**Property:**

GET /sessions/today returns sessions where started_at ∈ [today's UTC 00:00:00, tomorrow's UTC 00:00:00).

**Implies:**
- Test file: tests/test_session_history.py
