## Scenario 004: Marcus closes app during session; /complete never called (abandoned session)

**Severity:** degradation

**Setup:**

Marcus started session 5 minutes ago. Session_id in database with started_at. Marcus force-quits app.

**Trigger:**

Frontend dies. /complete never called.

**Expected:**

Per contract: abandoned sessions not persisted. GET /sessions/today does NOT include abandoned session_id.

**Concern:**

Contract ambiguity: /start returns session_id—is it ephemeral or DB-generated? If in DB, query must filter NULL completed_at.

**Property:**

GET /sessions/today returns only sessions where completed_at IS NOT NULL.

**Implies:**
- Test file: tests/test_sessions_lifecycle.py
- Implies architectural clarification: are session records written on /start or on /complete?
