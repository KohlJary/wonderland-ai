## Ticket 009: Display weekly and all-time history summary

**Sources:** review-weekly-and-all-time-history
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1-1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: session-persistence
- Soft: —

**Description:**

Separate view (tab or collapsible section): show a summary of sessions from the past 7 days and a career total (all sessions ever recorded). Render as simple numbers: total sessions, total hours, maybe a rough day-by-day breakdown. No fancy charts yet; text and numbers are fine. Query IndexedDB: all records in the past 7 days, all records ever.

**Acceptance:**
- Weekly summary shows sessions and hours from past 7 days
- All-time summary shows career totals
- Queries are efficient (no N+1, no full-table scans)

**Risk:**

If the user has thousands of sessions recorded, queries could slow down. Mitigation: add indices to IndexedDB schema in ticket 2; denormalize aggregates if needed in a future ticket.
