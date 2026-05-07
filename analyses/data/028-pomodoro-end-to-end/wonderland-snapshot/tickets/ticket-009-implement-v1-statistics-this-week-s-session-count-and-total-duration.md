## Ticket 009: Implement v1 statistics—this week's session count and total duration

**Sources:** view-this-week-s-and-all-time-session-statistics
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.5–1 day, 75% confident
**Status:** open

**Dependencies:**
- Blocks: statistics-display-v1
- Blocked by: session-history-query
- Soft: —

**Description:**

Build a backend query that aggregates this week's sessions: total count and total duration (sum of all session times). Expose this via an API endpoint. This is the minimal statistics feature for v1—enough for the user to see their weekly effort at a glance.

**Acceptance:**
- Endpoint returns accurate count of sessions completed this week
- Endpoint returns accurate total duration of sessions this week
- Week boundary is clearly defined (e.g., Monday–Sunday)
- Calculation is correct even if sessions span midnight

**Risk:**

Week boundary definition—clarify whether week is Mon–Sun or Sun–Sat and whether it's based on user's local timezone or server timezone.
