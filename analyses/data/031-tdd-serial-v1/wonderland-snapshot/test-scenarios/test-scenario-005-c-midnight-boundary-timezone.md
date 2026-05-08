## Test Scenario 005-C: Midnight Boundary and Timezone Sensitivity

**Feature:** Streak or Gamification (Optional) — Feature 005
**Persona:** Kenji, college student in San Francisco (Pacific Time, UTC-8)
**Axis:** fragility, edge case, timezone handling, midnight boundary

### Setup

Kenji is in San Francisco (UTC-8). He completes a focus session late on Monday evening.
The session timestamp needs to be correctly attributed to Monday (in his local timezone),
not Tuesday (in UTC).

### Scenario

**Monday, January 1, 2024, 22:00 PT (10:00 UTC on January 2):**
- Kenji completes a 25-minute focus session
- Session completion timestamp: 2024-01-01T22:00:00 (in PT, his local time)
- OR: timestamp logged as 2024-01-02T06:00:00 UTC (with timezone info)
- Event log records this session

**Question:** Which day does this session count toward?
- **Kenji's perspective:** Monday, January 1 (his local time)
- **UTC perspective:** Tuesday, January 2 (server time)

### Observable Result

Kenji opens the app on Tuesday morning (PT) and checks the streak:
- **Correct:** Streak shows "1 day" (the Monday session counts)
- **Incorrect:** Streak shows "0 days" (the UTC-recorded Tuesday session doesn't count as a completed Monday)

### Acceptance

✓ Streak calculation respects user's local timezone, not UTC
✓ A session completed at 22:00 PT on Monday counts toward Monday, not Tuesday
✓ The midnight boundary is evaluated in the user's timezone, not UTC

### Failure Mode This Test Covers

**Timezone boundary condition:** If the backend logs timestamps in UTC without timezone awareness,
or if the frontend/backend disagree on how to interpret timestamps, streak calculation will be wrong
for users in non-UTC timezones.

This is especially critical for streak (daily boundary) and weekly reset (Monday boundary), which
are both timezone-dependent.

### Known Ambiguity

**Contract Note 005 says:**
> "Midnight boundary is critical: events must be tagged with completed_at timestamp in user's
> local time (or we sync on user's timezone, or we use UTC and frontend converts)."

Three options are listed, but not resolved:
1. **Backend stores local time:** Event log stores "2024-01-01T22:00:00" (PT) with zone info
2. **Sync on user's timezone:** Backend knows user's timezone (from Feature 004 settings) and can convert
3. **UTC + frontend converts:** Backend stores "2024-01-02T06:00:00Z" (UTC), frontend applies user's zone offset

Each option has different implications:

- **Option 1 (local time stored):** Backend query for "all sessions on Monday" needs to be timezone-aware
- **Option 2 (sync on user's timezone):** Requires Feature 004 (settings) to be complete; backend has user's timezone
- **Option 3 (UTC + frontend converts):** Frontend has all the logic to compute streak; backend just returns raw events

This test does NOT assume which option is chosen. It just verifies: **the streak calculation is correct
for the user's timezone.**

### Dependences

- Feature 001 (focus session timer): sessions have timestamps
- Feature 003 (event log): event log is queryable
- Feature 004 (persistent settings): user's timezone is stored (or fetched from system)
- **Contract decision:** How is timezone handled in the event log? (Option 1, 2, or 3 above)

### Ticket Reference

story-005, feature-005, contract-note-005
