## Ticket 005: Add weekly and all-time history view

**Sources:** review-weekly-and-all-time-history
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: add-session-history-view
- Soft: —

**Description:**

Add a 'History' tab or view accessible from main screen. Show sessions completed this week (grouped by day) and an all-time total. Include a simple chart or bar graph showing sessions per day for the past 7 days (optional but nice). Fetch data from backend; don't compute on frontend. The user should be able to glance at their focus patterns over time.

**Acceptance:**
- History view shows completed sessions grouped by date (this week)
- All-time session count is displayed
- User can navigate between main timer view and history view
- Data is fresh (reflects most recent session on load)

**Risk:**

Chart rendering library choice — defer if no quick consensus. Start with a table; add chart in fast-follow.
