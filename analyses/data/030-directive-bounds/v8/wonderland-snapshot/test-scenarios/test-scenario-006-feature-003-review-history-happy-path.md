## Test Scenario 006: Review history happy path (Feature 003)

**Feature:** Review session history
**Persona:** Marcus, tracking his focus streak over a week
**Severity:** critical

**Scenario:**

Marcus completes three focus sessions (25+5 each, 30 minutes total per session). Each session is written to the database on completion. Marcus opens the history view. The backend returns GET /api/sessions (or /api/sessions/history) with all three sessions, ordered most-recent-first. Each session record includes: started_at, completed_at, focus_duration, break_duration, total_time_focused. Marcus can see his three sessions listed and compute patterns (e.g., "I focused 75 minutes today").

**What breaks if this fails:**

Marcus has no visibility into his patterns, defeating the motivation-through-visibility value of the feature.

**Acceptance Criteria:**

- GET /api/sessions returns 200 with list of completed sessions for the session_id
- Each session has: {session_id, started_at, completed_at, focus_duration, break_duration, created_at}
- List is ordered by started_at DESC (most recent first)
- Total sessions count matches expected (3 in this case)
- Completed sessions are queryable immediately after session completion event (no batching delay)
