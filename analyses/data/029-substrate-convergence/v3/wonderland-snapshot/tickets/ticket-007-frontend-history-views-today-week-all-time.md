## Ticket 007: Frontend history views: today, week, all-time

**Sources:** story:review-today-s-session-count, story:review-weekly-and-all-time-history
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket:history-append-only-log-and-session-aggregation
- Soft: —

**Description:**

Three tabs or a selector: Today | Week | All-time. Each tab calls GET /history/[today|week|all-time], displays counts, durations, averages. Simple card layout: "X focus sessions today, Y min total, Z min average. A break sessions, B min total, C min average." Pull-to-refresh. No charts in v1.

**Acceptance:**
- Today tab displays today's session count, total duration, average session length
- Week tab displays last 7 days' stats
- All-time tab displays cumulative stats
- Pull-to-refresh updates stats
- Stats refresh on navigation back to History tab

**Risk:**

Low. Straightforward data display.
