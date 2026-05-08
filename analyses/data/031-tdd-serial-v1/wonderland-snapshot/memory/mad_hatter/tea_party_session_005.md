# Tea Party Session — Feature 005 (Streak or Gamification)

**Date:** M4, iteration 5/5
**Feature:** streak-or-gamification-optional (Feature 005)
**Artifacts:** test-scenario-005-a, test-scenario-005-b, test_streak_happy_path.py, test_streak_fragility.py

## What I Shipped

**Test Scenarios (Alice + Hatter):**
1. **005-a (Alice's happy path):** Kenji completes 3 sessions across Mon-Wed, opens daily review Wed evening, sees "3 sessions this week" — the motivating signal. Depends on Feature 001 (sessions work) and Feature 003 (event log exists).

2. **005-b (Hatter's failure modes):** Four failure-mode axes:
   - Midnight boundary: session at 23:59 local time must count toward that day, not next (timezone sensitivity)
   - Streak reset: what does "consecutive days" mean? Does Thu skip break streak? When does count reset?
   - Data consistency: concurrent completions, event log query integrity
   - Offline loss: uninstall/reinstall, network failures

**Test Files:**
- `tests/test_streak_happy_path.py`: 3 tests, all skip pending contract clarity + Feature 003 fixtures
- `tests/test_streak_fragility.py`: 3 test classes with 14 named subcases, all skip pending contract clarity + Feature 003 fixtures

## Contract Ambiguities Blocking M5

**AMBIGUITY 1: Weekly Count vs. Daily Streak**
- Story-005 language: "how many focus sessions I've completed THIS WEEK" = weekly count (ISO week rolling, reset Monday)
- Contract-note-005 language: "consecutive days with ≥1 session" = daily streak (resets on skip)
- Different calculations, different UX, different motivation signal for Kenji
- Example: Mon/Tue/Wed sessions + Fri (skip Thu) = 4 total for the week, OR streak is 1 day (broken Thu, reset Fri)
- Which one is this feature? Need explicit choice.

**AMBIGUITY 2: Timezone Conversion Ownership**
- Problem (per contract-note): "midnight boundary is critical" — user in PT completing session 23:59 PT must count toward PT day, not UTC day (would be 07:59 UTC next morning, wrong day)
- Solution (not specified): Who converts? Backend? Frontend? Where does timezone come from (Feature 004 settings?)? When?
- Risk: if wrong, streak silently breaks for PT/PT/ET/etc users, while working for UTC users
- Scenario 005-b::TestMidnightBoundary will catch the bug IF contract specifies the approach

## Implications for M5

Tests are ready and will run once:
1. Feature 003 provides event log + insertion fixtures (Tweedledum implements in Feature 003 M5)
2. Contract-note-005 resolves both ambiguities

Until then: all tests skip with explicit error messages pointing to the blockers. No hidden failures.

## Hatter's Judgment

These aren't edge cases or "nice to have" tests. They are the load-bearing questions:
- Which feature is this actually building? (ambiguity 1)
- Will it corrupt user data silently? (ambiguity 2)

The test surface is complete. The contract needs to be.
