## Test Scenario: Settings update persists focus_minutes and break_minutes to DB

**Severity:** breakage

**Feature:** Feature 002: Customize session and break lengths

**Setup:**

User has session_id=yuki-s1. Settings table is empty (first time setting custom durations). Frontend calls POST /settings with {focus_minutes: 45, break_minutes: 10}.

**Trigger:**

Backend receives settings update request, executes upsert logic (update if row exists for user, insert if not).

**Expected:**

Backend writes to settings table: {session_id: yuki-s1, focus_minutes: 45, break_minutes: 10, updated_at: now}. Returns 200 with full settings object. Next call to GET /settings returns same values.

**Concern:**

If upsert logic is broken (always INSERT instead of UPDATE, or always UPDATE and fails on first write), data either duplicates (multiple rows per user) or is lost (INSERT fails on second update). Silent-wrongness if read returns old values while DB has new ones, or never saves at all.

**Property:**

For all settings updates U on session_id S with durations (F, B), the settings table contains exactly one row for S with focus_minutes=F and break_minutes=B.

**Implications:**

None noted.
