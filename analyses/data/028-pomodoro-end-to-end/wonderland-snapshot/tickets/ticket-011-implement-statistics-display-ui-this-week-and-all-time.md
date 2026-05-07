## Ticket 011: Implement statistics display UI—this week and all-time

**Sources:** view-this-week-s-and-all-time-session-statistics
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.75–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: session-statistics-v1-week, session-statistics-all-time
- Soft: —

**Description:**

Build a frontend view that displays this week's and all-time statistics side by side. Show session count and total duration for each period in a clear, scannable format. This could be a simple two-column layout or a pair of cards.

**Acceptance:**
- Statistics are displayed in a clear, scannable format
- This week's session count and duration are visible
- All-time session count and duration are visible
- Numbers update in real time or refresh when the user navigates to the view
- UI is responsive on mobile and desktop

**Risk:**

Real-time updates might be difficult if there are multiple browser tabs open; consider eventual consistency or a refresh button.
