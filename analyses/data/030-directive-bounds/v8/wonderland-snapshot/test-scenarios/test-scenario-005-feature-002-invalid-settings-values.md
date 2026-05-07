## Test Scenario 005: Invalid settings values rejected (Feature 002)

**Feature:** Customize session and break lengths
**Severity:** high

**Scenario:**

Yuki (or a test client) sends settings update with focus_minutes=0 or break_minutes=-1 or focus_minutes="abc" (type error). The backend rejects with 400 Bad Request + validation error.

**What breaks if this fails:**

Invalid settings poison the database, and subsequent session starts using invalid defaults create incoherent sessions.

**Acceptance Criteria:**

- POST /api/settings with focus_minutes=0 returns 400 "focus_minutes must be >= 1"
- POST /api/settings with break_minutes=-1 returns 400 "break_minutes must be >= 0" (breaks can be 0 for no break)
- POST /api/settings with focus_minutes="abc" returns 400 with type mismatch error
- POST /api/settings with missing focus_minutes or break_minutes returns 400 "required field"
- Settings table is not modified by any invalid request
