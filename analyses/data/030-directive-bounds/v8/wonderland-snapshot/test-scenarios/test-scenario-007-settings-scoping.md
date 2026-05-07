## Test Scenario: GET /settings returns settings for the session, not for a different session

**Severity:** silent-wrongness

**Feature:** Feature 002: Customize session and break lengths

**Setup:**

Two users: alice-s1 with settings (30, 5), yuki-s1 with settings (45, 10). Frontend sends GET /settings with header X-Session-Id: yuki-s1.

**Trigger:**

Backend queries settings for yuki-s1.

**Expected:**

Response is {focus_minutes: 45, break_minutes: 10, ...}. Not alice's settings.

**Concern:**

If settings scoping by session_id is missing (no WHERE clause filtering), query returns wrong user's settings. User sees settings belonging to a previous session or browser tab. Or if session_id is not being passed through the API, server returns a single 'default' settings row that all sessions share.

**Property:**

For all GET /settings requests with session_id S, the response contains settings associated with S, never with any other session_id.

**Implications:**

None noted.
