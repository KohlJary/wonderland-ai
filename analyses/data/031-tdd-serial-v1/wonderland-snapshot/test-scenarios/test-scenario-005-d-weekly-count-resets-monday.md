## Test Scenario 005-D: Weekly Session Count Resets on Monday

**Feature:** Streak or Gamification (Optional) — Feature 005
**Persona:** Kenji, 19, college student, responds well to visible progress markers
**Axis:** happy path, weekly reset, calendar boundary

### Setup

Kenji completes 5 focus sessions in Week 1 (Jan 1-7, ISO week 1, Monday-Sunday).
On Monday of Week 2 (Jan 8), he expects the weekly counter to reset to 0.

### Scenario

**Week 1 (ISO Week 1: Monday Jan 1 - Sunday Jan 7):**
- Mon Jan 1: 2 sessions completed
- Tue Jan 2: 1 session completed
- Wed Jan 3: 2 sessions completed
- Thu Jan 4 - Sun Jan 7: 0 sessions completed
- **Weekly count for Week 1:** 5 sessions

Friday Jan 5, 20:00: Kenji checks the daily review and sees "5 sessions this week"

**Transition to Week 2:**
- At midnight on Sunday Jan 7 (or at the start of Monday Jan 8, 00:00):
  - Weekly counter resets to 0

**Week 2 (ISO Week 2: Monday Jan 8 - ...):**
- Mon Jan 8, 09:00: Kenji completes 1 session
- **Weekly count for Week 2:** 1 session

Mon Jan 8, 20:00: Kenji checks the daily review and sees "1 session this week" (not 6)

### Observable Result

The weekly session count is:
- **End of Week 1:** "5 sessions this week"
- **Start of Week 2 (after Monday 00:00):** "0 sessions this week" or "1 session this week" (depending on whether Kenji has completed a session Monday)
- **Note:** The counter does not accumulate across weeks; it resets to 0 at the ISO week boundary

### Acceptance

✓ Weekly counter shows correct ISO week aggregation
✓ Counter resets at Monday 00:00 (ISO week boundary)
✓ Counter does not carry over from one week to the next

### Failure Mode This Test Covers

**Week boundary calculation:** If the weekly reset is incorrect (e.g., resets on Sunday instead of Monday,
or accumulates across weeks without resetting), the motivational signal breaks (Kenji sees inflated counts).

### Known Ambiguity

**Contract Note 005 specifies:**
> "Weekly view shows session count for the current week (ISO week, rolling)."

ISO week is defined, but the boundary might vary by timezone:
- **Option 1 (UTC weeks):** Monday 00:00 UTC is the reset boundary globally
- **Option 2 (Local timezone weeks):** Monday 00:00 in the user's timezone is the reset boundary

For Kenji in San Francisco (PT), these are different:
- UTC: Monday 00:00 UTC = Sunday 16:00 PT
- PT: Monday 00:00 PT = Monday 08:00 UTC

This test assumes **Option 2 (local timezone)**: Kenji's week resets at Monday 00:00 PT (his local time),
not at Monday 00:00 UTC.

### Dependences

- Feature 001 (focus session timer): sessions have timestamps
- Feature 003 (event log): events are logged with timestamps
- Event log query: backend can return all sessions for a given ISO week
- **Contract decision:** Is the week boundary UTC or local timezone? (Likely local, but not explicitly stated)

### Ticket Reference

story-005, feature-005, contract-note-005
