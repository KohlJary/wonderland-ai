## Scenario 030: Derek flies PT→London overnight (same UTC, different local dates), midnight boundary

**Severity:** degradation

**Setup:**

Derek builds 5-day streak in PT. Friday 23:59 PT (Sat 07:59 UTC): completes session. Flies to London. Sat 08:00 London (still Sat UTC, confusion about local time).

**Trigger:**

Derek opens app Sat morning London time. Frontend queries streak.

**Expected:**

Streak continues correctly using London local time (Sat = Sat UTC, Sun = Sun UTC, no ambiguity). Derek sees streak active.

**Concern:**

If system assumes 'timezone always PT' or conflates local with UTC, Derek's Sat UTC session gets attributed to Sun London or vice versa. Rare but possible at timezone boundary.

**Property:**

Streak calculation invariant to user's physical location. Only timezone setting matters, not geography.

**Implies:**
- Implies decision: home-timezone (always PT) or current-device-timezone (changes when user moves)?
- Implies test fixture: simulate user timezone changes
