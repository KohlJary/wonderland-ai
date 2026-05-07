## Test Scenario 004: Customize settings happy path (Feature 002)

**Feature:** Customize session and break lengths
**Persona:** Yuki, student with nonstandard focus rhythm (45min work, 10min break)
**Severity:** critical

**Scenario:**

Yuki opens settings and changes focus_minutes from 25 to 45 and break_minutes from 5 to 10. The backend receives POST /api/settings {focus_minutes: 45, break_minutes: 10}, persists to the settings table (upserting the single row per session_id), and returns {focus_minutes: 45, break_minutes: 10, updated_at: timestamp}. The frontend caches this. On app restart, the frontend calls GET /api/settings and loads the same values. When Yuki starts a new session, it defaults to 45/10 unless overridden.

**What breaks if this fails:**

Settings changes are lost on app restart, or worse, silently reverted to defaults, frustrating users who have explicitly configured the app for their rhythm.

**Acceptance Criteria:**

- POST /api/settings with {focus_minutes: 45, break_minutes: 10} returns 200 with same values + updated_at timestamp
- Database settings table now has a row with session_id, focus_minutes=45, break_minutes=10
- GET /api/settings for same session_id returns {focus_minutes: 45, break_minutes: 10, updated_at: <timestamp from previous POST>}
- POST /api/sessions/start without explicit durations uses settings values (45/10)
- settings table has exactly one row per session_id (upsert semantics, not duplicate rows)
