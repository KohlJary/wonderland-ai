## Ticket 010: Implement all-time statistics—total session count and duration

**Sources:** view-this-week-s-and-all-time-session-statistics
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: statistics-display-v1
- Blocked by: session-history-query
- Soft: —

**Description:**

Build a backend query that aggregates all sessions ever logged by the user: total count and total duration. Expose this via an API endpoint. This shows the user the total scope of their tracking since they started using the app.

**Acceptance:**
- Endpoint returns accurate count of all sessions ever logged
- Endpoint returns accurate total duration across all sessions
- Query is performant even for users with thousands of sessions

**Risk:**

If the user has thousands of sessions, the sum query could become slow; consider a materialized summary table if performance is an issue.
