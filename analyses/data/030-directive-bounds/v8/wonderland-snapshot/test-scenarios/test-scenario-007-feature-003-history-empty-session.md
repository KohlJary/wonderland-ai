## Test Scenario 007: History endpoint handles empty session gracefully (Feature 003)

**Feature:** Review session history
**Severity:** medium

**Scenario:**

A user (or session_id) has no completed sessions yet. The client calls GET /api/sessions/history. The backend returns a 200 with an empty list, not a 404 or error.

**What breaks if this fails:**

New users see an error instead of a blank history, creating a jarring experience on first load.

**Acceptance Criteria:**

- GET /api/sessions for a session_id with zero completed sessions returns 200 with empty list: []
- No 404 error or "not found" message
- Frontend can safely render an empty history view (e.g., "No sessions yet. Start one to begin tracking your focus.")
