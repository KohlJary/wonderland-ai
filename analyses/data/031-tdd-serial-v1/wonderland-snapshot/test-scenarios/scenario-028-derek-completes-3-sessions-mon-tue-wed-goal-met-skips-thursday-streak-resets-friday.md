## Scenario 028: Derek completes 3+ sessions Mon/Tue/Wed (goal met), skips Thursday, streak resets Friday

**Severity:** breakage

**Setup:**

Derek's goal: 3 completed sessions/day. Mon-Wed: 3 each day (streak=3). Thursday: 0 (skips). Friday: 3.

**Trigger:**

Friday evening, Derek opens daily review (shows streak + today's progress).

**Expected:**

Streak=1 (Friday only; Thursday broke chain). Progress=3/3 today. Derek sees reset is correct.

**Concern:**

Daily-streak logic differs from weekly-count. Derek's streak = consecutive days hitting goal (3 sessions), not total in week. If any day <3, chain breaks.

**Property:**

Derek_streak[day N] = Derek_streak[day N-1] + 1 if day N ≥3 sessions AND day N-1 ≥3, else 1 if day N ≥3, else 0.

**Implies:**
- Implies goal definition: 3 sessions or 75 minutes? Story 007 mentions both.
- Implies daily review augmentation: show streak AND today's progress-toward-goal
- Implies contract pick: Derek's daily-streak or Kenji's weekly-count
