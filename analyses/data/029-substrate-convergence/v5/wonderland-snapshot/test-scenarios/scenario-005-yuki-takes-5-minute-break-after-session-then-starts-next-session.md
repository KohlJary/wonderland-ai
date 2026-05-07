## Scenario 005: Yuki takes 5-minute break after session, then starts next session

**Severity:** breakage

**Setup:**

Yuki completed 25-minute session. Session record in DB with completed_at, completed_break_at=NULL. Frontend shows break UI.

**Trigger:**

Break timer counts down 300 seconds. Frontend POSTs /sessions/{id}/break-complete with {completed_at: <now>}. Frontend POSTs /sessions/start for next session.

**Expected:**

Backend accepts break-complete, updates completed_break_at field, returns 200 with full updated record. Next /sessions/start succeeds with new session_id.

**Concern:**

Backend might reject further updates on completed session, or return incomplete response forcing re-query.

**Property:**

For all sessions with completed_at NOT NULL, /break-complete sets completed_break_at. Response includes full updated session record.

**Implies:**
- Test file: tests/test_breaks_and_transitions.py
