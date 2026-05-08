## Scenario 027: Kenji completes three sessions in a week, sees 3-session count on daily review

**Severity:** breakage

**Setup:**

Kenji has Feature 001 (timer) + Feature 003 (event log). Mon Jan 1 - Wed Jan 3: one session each day.

**Trigger:**

Wednesday evening, Kenji opens daily review / streak display.

**Expected:**

Display shows 'Sessions this week: 3' or '🔥 3'. Visual progress marker. Kenji feels momentum.

**Concern:**

Weekly count aggregates all sessions in ISO week regardless of order. If Kenji does 2 Mon + 1 Fri, count = 3. Test confirms weekly aggregation, not daily-streak logic.

**Property:**

weekly_session_count(W) = sum of all completed-focus-sessions in ISO week W, regardless of order.

**Implies:**
- Implies contract pick: weekly-count or daily-streak? Story 005 says weekly; Story 007 says daily.
- Implies Feature 003: event log classifies sessions as focus/break, completed/skipped
- Implies backend query: 'all completed focus sessions in ISO week W'
