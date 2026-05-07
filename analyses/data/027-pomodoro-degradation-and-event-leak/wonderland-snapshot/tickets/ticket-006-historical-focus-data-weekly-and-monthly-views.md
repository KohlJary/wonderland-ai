## Ticket 006: Historical focus data: weekly and monthly views

**Sources:** review-historical-focus-data
**Owner:** tweedledee
**Tier:** fast-follow
**Estimate:** 2-3 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: persist-focus-session-to-indexeddb
- Soft: query-focus-sessions-for-daily-review

**Description:**

Query IndexedDB for sessions in past 7 days and past 30 days. Render summary stats: total sessions, total focus time, average session length, trend (is focus time increasing or decreasing week-over-week). Display as simple text summary or basic bar chart. No fancy visualization in MVP; clarity over aesthetics.

**Acceptance:**
- Weekly view shows past 7 days of data
- Monthly view shows past 30 days of data
- Trend calculation is accurate (can be simple: 'up', 'flat', 'down')
- Views load within 500ms

**Risk:**

If data set grows large, querying could slow. MVP: no pagination; assume < 200 sessions.
