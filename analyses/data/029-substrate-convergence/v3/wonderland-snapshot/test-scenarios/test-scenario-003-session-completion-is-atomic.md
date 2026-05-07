# Test Scenario 003: Session completion write is atomic (both SessionRecord and Session.status or neither)

**Severity:** breakage

**Setup:**

A session is running and about to complete. The database is accessible and the write should succeed. However, a constraint violation occurs mid-write (simulated to test atomicity).

**Trigger:**

The session's duration elapses. The backend attempts to:
1. Write a SessionRecord with (completed_at, session_duration_ms, break_duration_ms, session_type).
2. Update Session.status from 'running' to 'completed'.

A database constraint violation occurs partway through (simulated by injecting a failure).

**Expected:**

One of two outcomes occurs:
- **A (success):** Both the SessionRecord write and the Session.status update complete. History includes the completed session, and the next query for the session shows it as completed.
- **B (rollback):** Neither write completes due to the constraint violation. No SessionRecord is created, and Session.status remains 'running'. The session can be resumed and the write can be retried.

What should NOT happen:
- **X (partial success):** SessionRecord is written but Session.status is not updated. History shows a session that the UI thinks is still running.
- **Y (partial success):** Session.status is updated to 'completed' but no SessionRecord is written. The UI shows the session ended, but history queries return no record. When the user reviews history, the session is missing.

**Concern:**

If the transaction is not atomic:
- Sessions can be marked complete without a history record, causing the disappearing-session bug.
- Sessions can have a history record without being marked complete, causing the stuck-session bug.
- These bugs are silent (no error message), so users don't know their history is wrong.
- History aggregations (today's count, weekly chart) become incorrect and users lose trust.

**Property:**

For all session completions C:
- Either (SessionRecord(C) exists AND Session(C).status='completed') OR (SessionRecord(C) does not exist AND Session(C).status≠'completed').
- No partial state: never (SessionRecord exists AND Session.status='running') or (SessionRecord absent AND Session.status='completed').

**Implies:**

- Implies database transaction handling at the Session completion write point — flag for Tweedledum.
- Implies constraint and error handling strategy (what errors cause rollback vs. retry) — flag for Tweedledum.
