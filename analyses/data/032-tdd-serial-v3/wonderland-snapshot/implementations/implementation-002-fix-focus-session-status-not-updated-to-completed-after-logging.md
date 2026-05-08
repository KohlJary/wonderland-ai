## Implementation 002: Fix focus session status not updated to COMPLETED after logging

**Side:** backend
**Ticket:** ticket-004
**Contract:** sessions API v1 — POST /sessions/log now updates Session.status as a side effect
**Ready for review:** yes

**Approach:**

After logging a session to SessionLog (persistent history), now also update the in-progress Session record from RUNNING to COMPLETED. This ensures the sessions table reflects the true status. Added symmetric code for both focus and break session types (lines 184–205).

**Files:**
- src/backend/api/sessions.py: log_session() now updates Session records to COMPLETED (lines 184–205 in log_session function)
