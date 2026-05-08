# Implementation: Streak Display — Contract Clarity Required

**Feature:** Streak or Gamification (Optional) — Feature 005
**Status:** BLOCKED ON CONTRACT

---

## Summary

Tweedledum has raised two blocking contract ambiguities in Feature 005. I cannot implement the frontend streak display until both are resolved.

The tests are ready (test_streak_happy_path.py, test_streak_fragility.py). The test files document exactly what each interpretation would require. M5 cannot proceed until the contract chooses.

---

## Contract Ambiguity 1: Weekly Count vs. Daily Streak

**The Story (Alice, story-005):**
> "As Kenji, I want to see **how many focus sessions I've completed this week**, so that I can feel the momentum of consistency and stay motivated."

Plain language: "how many sessions THIS WEEK" = weekly aggregation (reset Monday, count all sessions in ISO week).

**The Contract Note (current):**
> "Streak counts **consecutive days** on which at least one focus session was completed. Count resets if a day passes with zero completed focus sessions."

Plain language: "consecutive days" = daily streak (count the number of days in a row with ≥1 session, reset to 0 if any day has zero).

**These are fundamentally different features.**

### Weekly Count (Kenji's need)
- **User journey:** Mon 2 sessions, Tue 1, Wed 0, Thu 3, Fri 0 → "4 sessions this week"
- **Reset:** Monday 00:00 (ISO week boundary)
- **Display:** "4 sessions completed this week" or "Sessions this week: 4"
- **Motivation signal:** "I did 4 real sessions; that's progress even if Mon/Thu weren't consecutive"

### Daily Streak (Contract's interpretation)
- **User journey:** Mon 2 sessions, Tue 1, Wed 0, Thu 3, Fri 0 → streak is BROKEN on Wed (0 sessions) → Thu starts a new 1-day streak
- **Reset:** Immediately when a day passes with 0 sessions
- **Display:** "1-day streak" (or "3-day streak" if it's Mon/Tue/Wed with Thu breaking it)
- **Motivation signal:** "You need to show up EVERY day or you lose your count"

**Frontend impact (Tweedledee):**
- Weekly count: query event log for past 7 days (or current ISO week), sum all completed sessions → single number
- Daily streak: query event log, find last N consecutive days with ≥1 session each, count N → single number
- UI states differ: weekly-count display is "X sessions this week"; daily-streak display is "X-day streak"
- Data persistence differs: weekly needs nothing (compute on-demand); daily streak might cache "last_completion_date" locally

**Proposal:** Resolve in contract-note-005 with explicit choice:

```
CHOICE A: Weekly Session Count (matches story-005 language)
- Display: "X sessions completed this week"
- Reset: Monday 00:00 (ISO week boundary)
- Calculation: sum of all completed sessions in current ISO week
- Motivation: consistency without pressure (can miss days, only total counts)

CHOICE B: Daily Consecutive-Day Streak (matches current contract language)
- Display: "X-day streak"
- Reset: immediately when any day passes with 0 sessions
- Calculation: count consecutive days from today backward, stop when hitting a day with 0 sessions
- Motivation: shows consecutive commitment (pressure to show up every day)

CHOICE C: Both (weekly count AND daily streak)
- Display both metrics on the same screen
- Reset times differ: weekly resets Monday; daily resets whenever a day is skipped
- Calculation: both run in parallel
- Motivation: user can see both "4 sessions this week" (total progress) and "1-day streak" (current momentum)
```

**My recommendation:** CHOICE A (weekly count only) because:
- Matches story-005's plain-language need ("this week")
- Kenji's persona is "easily distracted" — a daily-streak feature would be demoralizing (he'd break it often)
- Story's tone is "mirror, not report card" — weekly count is mirrors; daily streak is pressure
- Fast-follow scope: CHOICE C (both) would double the frontend/backend complexity; CHOICE A ships the core need

---

## Contract Ambiguity 2: Timezone Handling for Midnight Boundary

**The Problem:**
Contract-note-005 says: "midnight boundary is critical; events must be tagged with completed_at timestamp in user's local time (or we sync on user's timezone, or we use UTC and frontend converts)."

Three options are listed, none chosen.

**Example:**
- Kenji is in Pacific Time (UTC-8)
- Kenji completes a session at **23:59 PT on Jan 1**
- In UTC, this is **07:59 UTC on Jan 2**
- If backend uses UTC-only: session is logged as "Jan 2" → Kenji's streak/weekly-count breaks silently (session counted toward wrong day)
- If backend uses PT (user's local tz): session is logged as "Jan 1" → correct

**Frontend impact (Tweedledee):**
- If backend converts: my API contract just says `completed_at: ISO8601-with-timezone` and I can trust it's already in user's local perspective
- If frontend converts: I need to know user's timezone (from Feature 004 Persistent Settings), apply it to all timestamps from the backend before calculating
- If neither converts: silent data corruption

**Proposed solutions:**

```
OPTION A: Backend converts to user's local timezone before storing
- Event log stores: completed_at with timezone info (ISO8601-with-offset, or explicit timezone field)
- Backend reads user's timezone from Feature 004 Persistent Settings
- Backend converts event.timestamp to user_tz before writing to log
- Frontend reads: completed_at is already in user's local time, no conversion needed
- Frontend impact: simple, low-risk

OPTION B: Backend stores UTC only, frontend converts
- Event log stores: completed_at in UTC (ISO8601-with-Z)
- Backend provides: event.completed_at_utc + user.timezone (or frontend queries settings)
- Frontend reads: UTC timestamp + user timezone (from Feature 004 settings)
- Frontend calculates: "what local day does this UTC timestamp belong to in user's tz?"
- Frontend impact: more logic, more places for bugs, but gives frontend full autonomy

OPTION C: API contract specifies the seam explicitly
- Backend provides an endpoint: GET /api/events/for_streak?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD (in user's local date)
- Backend does all the timezone conversion internally
- Backend returns: list of sessions grouped by local date
- Frontend impact: simplest (just iterate dates and count), but less flexibility for caching/offline

```

**My recommendation:** OPTION A (backend converts before storing) because:
- Backend is source of truth for the event log; conversion should happen there
- Reduces frontend complexity and bug surface
- Feature 004 already knows user's timezone, so backend can access it
- ISO8601 timestamps with offsets are standard; timezone isn't "hidden"

---

## What I Cannot Do Until Contract Resolves

1. **Determine UI states.** If it's weekly count, the states are {loading, empty, "0 sessions this week", "4 sessions this week"}. If it's daily streak, the states are {loading, empty, "at risk", "1-day streak", "5-day streak"}. Different UI.

2. **Implement client-state management.** Weekly count needs minimal state (re-compute on-demand). Daily streak might cache last_completion_date locally to avoid querying on every render.

3. **Choose the API contract.** Weekly needs `GET /api/weekly_count`. Daily streak needs `GET /api/streak` (returns `{streak_days, last_completion_date}`). CHOICE C needs both.

4. **Write the implementation artifact.** I need to know what I'm building before I ship code.

---

## What the Tests Document

The test files (test_streak_happy_path.py, test_streak_fragility.py) already document both interpretations:
- 005-a (happy path) assumes weekly count → "3 sessions this week"
- 005-b (fragility) assumes daily streak → midnight boundary, streak reset, consecutive-day logic

Once the contract chooses, I will unskip tests matching that choice and skip tests for the unchosen path.

---

## Ticket Reference

Feature 005, story-005, contract-note-005
