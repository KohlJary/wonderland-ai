## Test Scenario 005-D: Timezone and Midnight Boundary for Streak Calculation

**Feature:** Streak or Gamification (Optional) — Feature 005
**Axis:** fragility, timezone handling, midnight boundary, cross-timezone sync

**Severity:** SILENT-WRONGNESS — if timestamps are not properly localized, Derek's streak will silently jump, break, or reset at unexpected times.

### The Problem

Contract Note 005 says: "Midnight boundary is critical; events must be tagged with completed_at timestamp in user's local time (or we sync on user's timezone, or we use UTC and frontend converts)."

If backend stores all timestamps in UTC but computes streak by calendar date without timezone conversion, a session completed at "23:00 PT" (11pm Pacific Time) will be stored as "07:00 UTC+1" (next UTC day) and attributed to the wrong calendar day.

Derek in Pacific Time:
- Completes a session at 23:59 PT on Monday = 07:59 UTC on Tuesday
- Event log stores: `completed_at=2024-01-02T07:59:00Z` (UTC)
- Backend query for "Monday sessions" uses `.date()` in UTC timezone
- Result: no sessions found on Monday (in UTC), streak breaks

### Scenario D1: Session at 23:59 PT logs correctly to local calendar day

**Setup:**
- Derek is in Pacific Time (UTC-8)
- Derek builds a 3-day streak: Friday, Saturday, Sunday (all PT)
- Feature 003 event log stores completed_at in ISO8601 with UTC timezone
- Monday evening, Derek has completed 2 sessions so far (not his goal of 3)

**Action:**
- Monday 23:59 PT: Derek completes his third session (hitting goal)
- Event is logged: `[id=X, completed_at=2024-01-02T07:59:00Z, type='focus', completion_type='timeout']`
- This timestamp is Tuesday 07:59 UTC

**Expected Result:**
- Streak query for "Monday PT" should return 3 sessions
- Streak does NOT break (Monday has ≥3 sessions, goal is hit)
- Tuesday morning PT, Derek's streak still shows 4 (Fri + Sat + Sun + Mon)

**Actual Result (if bug):**
- Backend uses UTC date without timezone conversion
- Query for "Monday" in UTC timezone finds 0 sessions (all are on Tuesday UTC)
- Streak calculation sees: Sunday (0 sessions) — breaks
- Streak is now 1 (reset Monday, only yesterday had sessions)
- Derek is confused: "I completed my goal Monday night, why did my streak reset?"

### Scenario D2: Session at 00:01 PT on next calendar day

**Setup:**
- Derek completes sessions Mon, Tue, Wed (each day ≥3 completed)
- Streak is 3 on Wednesday evening
- Thursday morning 00:01 PT: Derek completes his first session

**Action:**
- Thursday 00:01 PT = Thursday 08:01 UTC
- Event is logged: `[id=Y, completed_at=2024-01-04T08:01:00Z, type='focus']`

**Expected Result:**
- This session counts toward Thursday PT (the day user intended)
- Streak becomes 4 (Mon + Tue + Wed + Thu)

**Actual Result (if bug, same as D1):**
- Backend uses UTC date; 08:01 UTC is still Thursday UTC
- This case might actually work (by coincidence), but it's fragile
- If Derek's day starts with a session at 00:30 PT, it will be on Thursday UTC, so it works
- But if Derek has a session at 23:30 PT, it will be on Friday UTC, and could break

### Scenario D3: User crosses timezone mid-streak

**Setup:**
- Derek has built a 5-day streak in Pacific Time (PT, UTC-8)
- Friday PT evening, streak = 5
- Derek flies to London (GMT, UTC+0, 8 hours ahead)
- Saturday morning London time = Friday night/Saturday very early in PT

**Action:**
- Saturday morning 08:00 London time = Friday 23:00 PT (still Friday locally from PT perspective, but Saturday GMT)
- Derek completes a session
- Event is logged with backend timestamp: `Saturday 08:00 UTC`

**Expected Result:**
- Session should count toward Derek's "Saturday" (his local calendar day in London)
- If backend uses UTC, it's Saturday UTC = Saturday — this works
- If backend doesn't convert timezones, it's ambiguous: which timezone determines the "day"?

**Clarification Needed:**
Should session attribution use:
- (a) User's timezone-at-completion time (PT when session completes, London if user moves), or
- (b) User's "home timezone" (always PT, even if in London), or
- (c) UTC (never ambiguous, but may feel wrong to user in different timezone)

**Current assumption:** Backend stores in UTC, frontend converts to user's current local timezone for display.

### Contract Ambiguity: How does backend know user's timezone?

Backend needs to know Derek's timezone to convert UTC timestamps to local calendar days.

**Options:**
1. Store timezone in settings (Feature 004: Persistent Settings must include user's timezone)
2. Infer from session timestamps (fragile, assumes consistent timezone)
3. Always use UTC for all calculations (no ambiguity, but UX feels wrong)
4. Store timezone WITH each session event (more data, more reliable)

**Current status:** Contract Note 005 doesn't specify. Feature 004 (Persistent Settings) must clarify if timezone is stored.

### Failure Mode: DST Transitions

**Scenario D4: Fall Back — repeated hour**

USA Eastern Time, Sunday November 5, 2023, 02:00 EDT → 01:00 EST (fall back one hour).
The hour 01:00-02:00 repeats.

Derek completes sessions at:
- 01:30 EDT (first occurrence, before fall back)
- 01:30 EST (second occurrence, after fall back, 1 hour later in UTC)

**Expected Result:**
Both sessions are recorded with different UTC timestamps (even though wall clock shows same time).
Streak calculation treats them as two sessions on two different times.

**Current assumption:** Backend using UTC timestamps handles this correctly (no ambiguity in UTC).

### Test Implementation Notes

See `tests/test_streak_fragility.py`:
- `TestStreakTimezoneFragility` class covers D1, D2, D3
- `TestStreakDSTTransitions` class covers D4

All tests currently skip pending:
1. Feature 004 (Persistent Settings) implementation: must store user's timezone
2. Event log schema: must support timezone-aware timestamps or explicit timezone field
3. Backend streak query: must localize UTC timestamps to user's timezone before computing calendar dates
4. Clarification on "home timezone" vs. "current timezone" for Derek's use case

### Recommended Implementation Path

1. **Feature 004 must include timezone setting:** `{focus_duration_ms, break_duration_ms, ..., timezone: 'America/Los_Angeles'}`
2. **Feature 003 event log must store completed_at in UTC:** No ambiguity at storage layer
3. **Feature 005 backend streak query must:**
   - Fetch user's timezone from Feature 004
   - Convert UTC completed_at timestamps to user's local date
   - Group by local date
   - Count sessions per date
   - Calculate consecutive-day streak

4. **Frontend must display in user's local timezone**, not UTC

### Ticket Reference

story-007, feature-005, contract-note-005, feature-004, ticket-streak-or-gamification-optional
