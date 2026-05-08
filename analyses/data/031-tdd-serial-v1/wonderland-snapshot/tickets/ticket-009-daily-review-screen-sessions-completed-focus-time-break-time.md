## Ticket 009: Daily review screen: sessions completed, focus time, break time

**Sources:** daily-session-review
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: daily-session-log-backend
- Soft: —

**Description:**

User-facing screen (or modal/sidebar) that shows today's summary. Number of sessions, total focus time, total break time. Optionally, a list of today's sessions with their durations and labels. Bind to the backend daily log API. Allow user to navigate to past dates and see their logs.

**Acceptance:**
- User opens Daily Review; sees today's stats (session count, focus time, break time)
- User can click a past date and see that day's stats
- Optionally, a list of today's sessions is visible with labels and durations

**Risk:**

Date picker UX and timezone handling. For v1, assume local device timezone; no multi-timezone support.
