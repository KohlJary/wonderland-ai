## Test Scenario 005-B: Kenji's Streak Breaks When He Skips a Day

**Feature:** Streak or Gamification (Optional) — Feature 005
**Persona:** Kenji, 19, college student, responds well to visible progress markers
**Axis:** fragility, edge case, streak reset semantics

### Setup

Kenji has completed 3 consecutive focus sessions (Mon, Tue, Wed) and his streak is showing as "3 days."
He has Feature 001 (focus session timer) and Feature 003 (event log) working.

### Scenario

**Monday (Day 1):**
- 09:00: Kenji completes one 25-minute focus session
- Event log: [session_id=uuid1, completed_at=Mon-09:00, type='timeout']
- Streak display: "1-day streak" or "Streak: 1"

**Tuesday (Day 2):**
- 14:30: Kenji completes one 25-minute focus session
- Event log: [session_id=uuid2, completed_at=Tue-14:30, type='timeout']
- Streak display: "2-day streak" or "Streak: 2"

**Wednesday (Day 3):**
- 19:00: Kenji completes one 25-minute focus session
- Event log: [session_id=uuid3, completed_at=Wed-19:00, type='timeout']
- Streak display: "3-day streak" or "Streak: 3"

**Thursday (Day 4):**
- Kenji does NOT complete any focus session (zero events logged for Thursday)

**Friday (Day 5):**
- 10:00: Kenji opens the app
- Streak display should now show: "1-day streak" or "Streak: 0" or "Streak broken"

### Observable Result

The streak counter resets because Thursday had zero sessions. The streak should be:
- **Option A (strict):** Streak = 0 (consecutive days resets on any gap)
- **Option B (lenient):** Streak = 1 (Friday's session starts a new streak; Thursday gap breaks the old one)
- **Option C (weekly-only):** Weekly count shows 2 (Mon, Tue, Wed = 3, but Wed was last session, so streak is "stale")

Contract Note 005 is ambiguous here. The current phrasing is:
> "Streak counts consecutive days on which at least one focus session was completed. Count resets if a day passes with zero completed focus sessions."

This suggests **Option A**: Thursday has zero sessions, so the streak (which required consecutive days with ≥1 session) resets. Kenji's Friday session is day 1 of a new streak.

### Acceptance

✓ Streak counter resets when a day passes with zero sessions
✓ User's Friday session does not continue the old streak (old streak is "broken")
✓ User can rebuild a new streak starting Friday

### Failure Mode This Test Covers

**Consecutive-day boundary:** The feature is called "Streak," which implies consecutive days. This test verifies the consecutive-day logic: one missed day = streak broken. This is the distinction from "weekly session count" (which only resets on Monday, not on skipped days).

### Known Ambiguity

**Contract Note 005 leaves open:**
- Does "streak resets" mean the counter goes to 0?
- Or does "streak is broken" mean the counter stalls and requires rebuilding?
- Or does the feature show both "weekly count" (3 sessions this week, unaffected by skips) and "current streak" (0, broken on Thursday)?

The test assumes: Streak = 0 (or "broken") after Friday opens; Kenji can rebuild by completing a session Friday.

### Dependences

- Feature 001 (focus session timer): sessions can be completed with timestamps
- Feature 003 (event log): completed sessions are logged
- Event log query: backend returns all sessions for the past N days
- **Contract decision:** Is streak a daily counter or a weekly counter? (This test assumes daily; if the answer is weekly, the test changes.)

### Ticket Reference

story-005, feature-005, contract-note-005
