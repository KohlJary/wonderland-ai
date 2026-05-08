## Test Scenario 005-C: Derek's Daily Streak with Goal-Based Reset

**Feature:** Streak or Gamification (Optional) — Feature 005
**Persona:** Derek, 27, backend engineer, builds morning routine around focus sessions
**Axis:** happy path user journey, goal-based streak logic, daily consistency tracking

### Story Reference

Story 007: Derek wants to see his "daily accumulated focus time" and his "streak of days where I hit my goal (three completed sessions per day)."

This scenario tests the daily-streak-with-goal interpretation of Feature 005, as distinct from Kenji's weekly-count interpretation.

### Setup

Derek commits to a morning routine: **three 25-minute focus sessions per day** = his daily goal.

Feature 001 (focus session timer) is working. Feature 003 (event log) is recording session completions.

Derek will build a streak by hitting his goal for consecutive days.

### Scenario: Derek hits his goal for 5 consecutive days

**Monday morning:**
- 08:00: Derek starts and completes Session 1 (25 min)
- 08:30: Derek starts and completes Session 2 (25 min)
- 09:00: Derek starts and completes Session 3 (25 min)
- Event log has 3 completed focus sessions on Monday
- Goal check: Monday has 3 completed sessions ✓

**Tuesday through Friday:** Derek repeats the same routine each day.
- Each day: 3 sessions completed
- Event log grows: Mon=3, Tue=3, Wed=3, Thu=3, Fri=3

**Friday evening:**
- Derek opens the Daily Review screen
- Expected display: "Streak: 5 days" or "🔥 5-day streak"
- Also displays: "You've completed 3/3 sessions today"

### Scenario: Derek misses a day; streak resets to 0

**Saturday morning:** Derek is too busy. He skips any sessions. 0 completions on Saturday.

**Sunday morning:** Derek returns and completes his 3 sessions.
- Event log on Sunday: 3 completed sessions
- BUT Saturday had 0 sessions.
- Streak calculation: "Yesterday (Saturday) had 0 sessions, so the consecutive chain is broken."
- Streak resets to 1 (only Sunday has sessions).

**Sunday evening:**
- Derek opens Daily Review
- Expected display: "Streak: 1 day" (new streak started on Sunday)
- NOT "Streak: 6 days" (the chain was broken on Saturday)

### Acceptance Criteria

✓ Streak increments when Derek completes at least N sessions (contract: N=3? unclear) on a calendar day
✓ Streak resets to 0 if a calendar day passes with fewer than N sessions
✓ After reset, completing N sessions on a new day starts a new streak (=1)
✓ Daily review shows both current streak AND today's progress toward goal (e.g., "3/3 sessions today")

### Observable Difference from Kenji's Story (005-A)

**Kenji (weekly count):**
- "Sessions this week: 3" (all sessions in ISO week, regardless of consecutive)
- No session order matters; if he does 2 Mon + 1 Fri, still counts as 3 for the week

**Derek (daily streak with goal):**
- "Streak: 3 days" (only consecutive days matter)
- If he does 2 Mon + 1 Fri, the streak breaks Tuesday (0 sessions), so Friday session starts a new streak of 1
- Goal threshold matters: "hit 3 completed sessions per day" is the streak condition

### Known Ambiguities

**Contract Ambiguity 1: Session count vs. time threshold**

Story 007 has two possible goals:
- (a) "At least 3 completed sessions per day" (Derek's opening statement)
- (b) "At least 75 minutes total per day" (Derek's acceptance criterion, "three sessions × 25 min = 75 min/day")

These are not the same if Derek varies session lengths. If Derek does 4 sessions of 20 minutes each = 80 minutes, does that hit the goal?

**Current assumption:** Goal is "at least 3 completed sessions per day". The total-time goal (75 min) is secondary and may be its own feature.

**Contract Ambiguity 2: Weekly vs. Daily**

Feature 005 has two possible implementations:
- (a) **Weekly session count** (Kenji's story 005): "How many sessions did I do this week?" Resets Monday. No streak logic.
- (b) **Daily streak with goal** (Derek's story 007): "How many consecutive days have I hit my goal?" Resets when goal is missed.

The contract note mentions both "consecutive days" and "weekly view," which doesn't clarify.

**Current assumption:** This scenario tests interpretation (b). The Tweedledee/Tweedledum contract note must pick which feature to implement (or if both).

### Dependences

- Feature 001 (focus session timer): sessions can be completed with timestamps
- Feature 003 (event log): completed sessions are logged with timestamp + type + completion_type (e.g., 'timeout' = ran to completion, 'skip' = user skipped early)
- Event log query: backend can return all sessions for a given date, filtered by type='focus' + completion_type != 'skip'

### Failure Modes NOT in This Scenario

This is the happy path for Derek's story. Fragility scenarios (midnight boundary, timezone, offline sync, data loss) are in test-scenario-005-b and test_streak_fragility.py.

### Test Implementation Notes

See `tests/test_streak_daily_happy_path.py`:
- `TestStreakDailyHappyPath` class covers Derek's story
- Tests verify: 1-day streak on first session, increments on consecutive days, resets on missed day, new streak after reset

Tests currently skip pending:
1. Feature 003 event log implementation and session-type filtering
2. Definition of "goal": exactly 3 sessions, or configurable, or time-based?
3. Backend streak endpoint that returns both current streak and goal progress

### Ticket Reference

story-007, feature-005, contract-note-005, ticket-streak-or-gamification-optional
