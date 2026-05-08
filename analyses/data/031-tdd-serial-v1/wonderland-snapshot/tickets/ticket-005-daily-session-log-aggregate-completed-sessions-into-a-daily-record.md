## Ticket 005: Daily session log: aggregate completed sessions into a daily record

**Sources:** daily-session-review
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: daily-review-frontend
- Blocked by: session-persistence-backend
- Soft: —

**Description:**

Backend endpoint/query that produces a daily summary: number of sessions completed, total focus time, total break time, session durations. Queries the session store for all sessions completed on a given day. No filtering by type, tag, or category yet — just raw aggregation. Expose via API for the frontend to query.

**Acceptance:**
- Query today's log: returns count of focus sessions, sum of focus time, sum of break time
- Query a past date: returns the same aggregates for that date
- If no sessions on a date, return zero counts (not an error)

**Risk:**

Query performance if the session store grows large. For v1, assume <1000 sessions/user/year. Optimize if observed.
