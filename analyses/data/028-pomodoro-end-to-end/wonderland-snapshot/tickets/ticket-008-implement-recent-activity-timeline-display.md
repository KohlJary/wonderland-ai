## Ticket 008: Implement recent activity timeline display

**Sources:** review-today-s-session-count-and-recent-activity
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.75–1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: session-history-query
- Soft: —

**Description:**

Build a frontend view showing recent sessions as a timeline or list. Each entry should show the session start time, duration, and break duration. Show today's sessions prominently at the top, followed by older sessions. This gives the user visibility into their recent work pattern.

**Acceptance:**
- Timeline displays today's sessions at the top
- Each session entry shows start time, duration, and break duration
- Older sessions are visible below today's sessions
- Timeline is scrollable if there are many sessions
- Times are displayed in the user's local timezone

**Risk:**

Timeline rendering performance if there are hundreds of entries; consider virtual scrolling.
