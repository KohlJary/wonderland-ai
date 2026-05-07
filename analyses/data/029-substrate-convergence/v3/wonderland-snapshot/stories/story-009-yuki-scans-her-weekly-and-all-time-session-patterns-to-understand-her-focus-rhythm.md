## Story 009: Yuki scans her weekly and all-time session patterns to understand her focus rhythm

**Persona:** Yuki, 31, data analyst, obsessive about personal metrics. She wants to see trends in how many sessions she completes, when she's most productive, how her focus time changes week-to-week.

**Situation:**

It's Friday afternoon. Yuki has been using the timer for three weeks. She opens the 'History' view to see a week-by-week breakdown and spot patterns (e.g., 'Do I do more sessions on Mondays?' or 'Am I doing fewer 25-min sessions and more 15-min sessions over time?').

**Need:**

As Yuki, I want to view historical session data aggregated by week and across all time, so that I can understand my focus patterns and spot trends.

**Acceptance:**
- The History view displays a 'This Week' section (Mon–Sun, current week) with session count and total duration.
- A 'Previous Weeks' section shows the last 4 weeks (or fewer if Yuki hasn't used the app that long) with the same aggregations.
- An 'All-Time' summary shows total sessions run and total duration ever recorded.
- Tapping or clicking a week opens a breakdown by day (how many sessions each day that week).

**Tier:** fast-follow

**Confusion-flags:**
- Does 'week' always mean Mon–Sun, or should it respect the user's locale (e.g., Sun–Sat in the US)? The acceptance criterion assumes Mon–Sun; that might be wrong for some users.
- Is there a graph/chart visualization, or just tables of numbers? 'View data' could mean either. Yuki (a data analyst) would probably prefer a chart, but the feature scope doesn't specify.
- When Yuki opens a day breakdown, does she see individual sessions (timestamp, duration), or just aggregate counts? The criterion stops at the week level.
- What if Yuki's session lengths vary wildly (some 15 min, some 50 min)? Should the view show min/max/average per week, or just total? The criterion doesn't capture this nuance.
