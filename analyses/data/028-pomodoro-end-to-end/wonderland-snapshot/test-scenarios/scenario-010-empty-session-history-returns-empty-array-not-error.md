## Scenario 010: Empty session history returns empty array, not error

**Severity:** degradation

**Setup:**

Elena just installed app. Zero completed sessions. Queries /sessions/history.

**Trigger:**

Endpoint called on fresh user.

**Expected:**

Returns HTTP 200 with [] (empty array). Not 404, 500, or default data.

**Concern:**

If assumes >= 1 session, throws error. App crashes on first launch.

**Property:**

For all users with session_count == 0, GET /sessions/history returns HTTP 200 with [].
