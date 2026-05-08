## Test Scenario 005-A: Kenji Completes Three Sessions in a Week, Sees Count

**Feature:** Streak or Gamification (Optional) — Feature 005
**Persona:** Kenji, 19, college student, responds well to visible progress markers
**Axis:** happy path, user journey, motivation signal

### Setup

Kenji uses the Focus Session Timer daily but inconsistently. He has completed
Feature 001 (focus session timer) and Feature 003 (daily review with event log).

### Scenario

**Monday (Day 1 of ISO Week):**
- 09:00: Kenji starts and completes one 25-minute focus session
- Event log records: [session_id=uuid1, completed_at=Mon-09:00, type='timeout']

**Tuesday (Day 2 of ISO Week):**
- 14:30: Kenji starts and completes one 25-minute focus session
- Event log records: [session_id=uuid2, completed_at=Tue-14:30, type='timeout']

**Wednesday (Day 3 of ISO Week):**
- 19:00: Kenji starts and completes one 25-minute focus session
- Event log records: [session_id=uuid3, completed_at=Wed-19:00, type='timeout']
- 20:00: Kenji opens the Daily Review screen

### Observable Result

Daily Review shows:
- "3 sessions completed this week" (or "Sessions this week: 3")
- Visual progress indicator (e.g., "🔥 3" or a filled circle count)
- User feels the momentum of consecutive days — this is the motivating signal

If the feature also displays streak (consecutive days with ≥1 session):
- "3-day streak" or "🔥 3 days"

If the feature displays weekly count separately:
- "Sessions this week: 3"
- "Current streak: 3 days" (if Monday-Tuesday-Wednesday are consecutive with no skips)

### Acceptance

✓ The display prominently shows a count (3)
✓ The count matches the number of sessions Kenji completed that week
✓ The design tone is motivating, not judgmental (per story-005 confusion-flag)

### Failure Mode This Test Does NOT Cover

This is the happy path — time flows forward, no network failures, Kenji
completes sessions consistently. See test_streak_fragility.py for edge cases
(midnight boundary, timezone, offline, etc.).

### Known Ambiguity

**Contract Note 005 is ambiguous on:**
- Is this a daily streak (consecutive days, resets on skip) or a weekly
  session count (total for the ISO week)?
- Should Kenji's Monday-Tuesday-Wednesday count as a "3-day streak"?
- Should he see both "3 sessions this week" AND "3-day streak" or just one?

Per story-005: Kenji wants to "see how many focus sessions I've completed
this week" — which suggests a weekly count, not a daily streak. But the
contract note says "consecutive days" — which suggests a daily streak.

**This test assumes the reading is: weekly session count (Monday-Wednesday
in an ISO week = 3 sessions completed that week). The daily streak calculation
is a separate concern, tested in fragility scenarios.**

### Dependences

- Feature 001 (focus session timer): sessions can be completed with timestamps
- Feature 003 (event log): completed sessions are logged with timestamp + type
- Event log query: backend can return all sessions for the past 7 days (or
  current ISO week)

### Ticket Reference

story-005, feature-005, contract-note-005
