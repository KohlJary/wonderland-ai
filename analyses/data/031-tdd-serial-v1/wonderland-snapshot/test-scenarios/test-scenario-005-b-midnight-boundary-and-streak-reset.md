## Test Scenario 005-B: Midnight Boundary and Streak Reset (Failure Modes)

**Feature:** Streak or Gamification (Optional) — Feature 005
**Axis:** fragility, midnight boundary, streak reset logic, data consistency
**Severity:** HIGH — if these fail, the streak count will be silently wrong

### Failure Mode: Midnight Boundary

**The Issue:**
The contract note says: "midnight boundary is critical; events must be tagged
with completed_at timestamp in user's local time (or we sync on user's
timezone, or we use UTC and frontend converts)."

If the backend uses UTC only and the user is in Pacific Time (UTC-8), a session
completed at 23:00 PT (07:00 UTC next day) will incorrectly count toward the
wrong day. The user completes a session at 11pm on Monday night, but the
backend logs it as Tuesday because it's using UTC. Streak calculation reads
Tuesday and sees no Monday completion, breaking the streak incorrectly.

### Scenario A1: Session at 23:59 local time counts toward today, not tomorrow

**Setup:**
- User is in PT (UTC-8)
- Event log stores completed_at as ISO8601 with UTC timezone
- User completes a session at 23:59 PT on Jan 1

**Action:**
- Session completes at 23:59 PT Jan 1 = 07:59 UTC Jan 2
- Event log records: [completed_at=2024-01-02T07:59:00Z, ...]
- Streak query runs at midnight PT = 08:00 UTC (also Jan 2 in UTC)

**Expected Result:**
Session should count toward Jan 1 (PT perspective), not Jan 2.
Streak for Jan 1 = 1 (this session counts).
Streak for Jan 2 = 0 (until user completes another session on Jan 2 PT).

**Actual Result (if bug):**
Backend uses `completed_at.date()` in UTC without timezone conversion.
Jan 2 (UTC) != Jan 1 (PT), so session is counted toward Jan 2.
Streak query sees: Jan 1 PT = no sessions (wrong!), Jan 2 PT = 1 session.
Streak breaks because Jan 1 has no sessions. **This is the bug.**

### Scenario A2: Session at 00:01 local time counts toward today, not yesterday

**Setup:**
- User is in PT (UTC-8)
- User completes a session at 00:01 PT on Jan 2

**Action:**
- Session completes at 00:01 PT Jan 2 = 08:01 UTC Jan 2
- Event log records: [completed_at=2024-01-02T08:01:00Z, ...]
- Streak query runs for Jan 2 (PT)

**Expected Result:**
Session should count toward Jan 2 (PT), not Jan 1.
Streak for Jan 2 = 1 (if no previous session) or 2+ (if Jan 1 had one).

**This is the "just after midnight" case, more rare but still critical.**

### Failure Mode: Streak Reset Logic

**The Issue:**
The contract says: "Streak counts consecutive days on which at least one
focus session was completed. Count resets if a day passes with zero completed
focus sessions."

But what does "a day passes with zero sessions" mean? Scenarios:
- **Scenario B1:** Streak is 5. Friday I don't complete any session. What is
  Saturday's streak? (0, or still 5?)
- **Scenario B2:** Streak is 5. Saturday morning, I haven't yet completed a
  session. Is the streak "at risk" (show warning), or still 5, or already 0?
- **Scenario B3:** Streak resets to 0 immediately at midnight on a skipped day,
  or only when I check the app?

### Scenario B1: Streak resets when user doesn't complete a session on a day

**Setup:**
- Jan 1-5 (Mon-Fri): User completes ≥1 session each day. Streak = 5.
- Jan 6 (Sat): User does not open the app, completes 0 sessions.

**Action:**
- Streak query runs on Jan 7 (Sun), looking at historical data.
- Backend looks for: consecutive days with ≥1 session.
- Jan 1, 2, 3, 4, 5 each have ≥1 session ✓
- Jan 6 has 0 sessions ✗
- Consecutive chain breaks at Jan 6.

**Expected Result:**
Streak on Jan 7 = 0 (broken on Jan 6, not yet reset).
Or: Streak on Jan 7 = 1 (if user completed a session on Jan 7).

**Clarification Needed:**
After a streak breaks, does the user immediately lose the count, or
does it show "streak broken, complete a session to restart"?

### Scenario B2: Streak at risk vs. already reset

**Setup:**
- Jan 1-5: Streak = 5
- Jan 6 (Sat) morning, 08:00 local time: User hasn't yet completed a session
- User opens the Daily Review screen

**Action:**
- Query: "What is my streak right now?"
- Streak calculation looks at yesterday (Jan 5): has ≥1 session ✓
- Streak calculation looks at today (Jan 6) so far: has 0 sessions (so far)

**Expected Result (design choice):**
Display "5-day streak, at risk" or "Streak: 5 (active but needs completion today)"?

Or: Display "0-day streak (completed a session yesterday but not today)"?

This is more of a UX question than a calculation bug, but it's important
for the motivational tone Kenji expects.

### Failure Mode: Event Log Data Consistency

**Scenario C1: Concurrent session completions lose a day**

**Setup:**
- User has two timer windows open (bug, but possible)
- Session A completes at exactly 23:59 Jan 1
- Session B completes at exactly 00:00 Jan 2 (one millisecond apart)

**Action:**
- Event log records both:
  - [id=A, completed_at=Jan-1T23:59:59Z, type='timeout']
  - [id=B, completed_at=Jan-2T00:00:00Z, type='timeout']
- Streak query runs on Jan 2 evening

**Expected Result:**
Both sessions log successfully. Streak calculation sees:
- Jan 1: 1 session ✓
- Jan 2: 1 session ✓
- Streak = 2 (consecutive)

**Known Limitation:**
The contract note (Feature 003) doesn't specify behavior if two sessions
complete at the exact same microsecond. Our test assumes they both log
with different timestamps (one on each side of midnight).

### Failure Mode: Uninstall/Reinstall Loss

**Scenario D1: User reinstalls, loses streak history**

**Setup:**
- User has built a 30-day streak (impressive!).
- User uninstalls the app.
- User reinstalls the app.

**Action:**
- All local data is gone (no cross-device persistence per contract).
- Event log is empty.
- Streak query returns 0.

**Expected Result:**
Streak is 0 (expected per contract: "Streak resets if user uninstalls/reinstalls").

**Known Limitation (documented):**
This is a design trade-off in v1. Future versions might sync to cloud or
use cross-device storage. For now, it's acceptable for "fast-follow" tier.

### Contract Ambiguities This Scenario Highlights

1. **Timezone handling:** How does backend know user's timezone? From Feature 004
   (Persistent Settings)? From the session event itself? Currently unspecified.

2. **Streak reset semantics:** Is it immediate at midnight (if user doesn't open
   the app, streak resets anyway)? Or only when user checks the app and we
   query the event log? Currently unspecified.

3. **Offline behavior:** If user completes a session offline (Feature 001 works
   offline), does it log to the event log on reconnect? Or is it lost? Currently
   unspecified in Feature 003.

4. **Weekly count vs. daily streak:** The story asks for "weekly session count"
   but the contract note mentions "consecutive days" (daily streak). These are
   different calculations. Currently ambiguous.

### Test Implementation Notes

See `tests/test_streak_fragility.py`:
- `TestMidnightBoundary` class covers A1, A2
- `TestStreakCalculation` class covers B1, B2, C1
- `TestDataConsistency` class covers C1
- `TestOfflineAndErrorRecovery` covers D1

All tests currently skip pending:
1. Feature 003 event log implementation (insertion fixtures)
2. Backend streak query endpoint specification
3. Timezone handling clarification from Feature 004 / contract-note-005

### Ticket Reference

feature-005, contract-note-005, ticket-streak-or-gamification-optional
