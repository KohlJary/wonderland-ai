## Test Scenario 007: Devon reviews today's session count (User Journey)

**Feature:** View session history and statistics (feature-003)
**Persona:** Devon, 41, consultant. Tracks his productivity as a focus-quality signal. Wants to know: "Did I get five sessions in today?"
**Stack span:** frontend + backend
**Severity:** high
**Concern:** User happiness — does Devon get a reliable, instant snapshot of his productivity at a glance?

**User Journey:**

It's 6 PM. Devon is wrapping up his workday. He opens the pomodoro app. On the main screen, he sees a summary at the top:

```
Today: 5 sessions
This week: 24 sessions
All-time: 847 sessions
```

The "Today: 5 sessions" number is large and prominent. Devon smiles — he hit his daily goal. He taps "Today" to dive deeper.

The app shows a list of today's sessions:
- Session 1: 25 min, completed at 9:15 AM
- Session 2: 25 min, completed at 10:05 AM
- Session 3: 25 min, completed at 11:15 AM
- Session 4: 25 min, completed at 1:30 PM
- Session 5: 25 min, completed at 3:15 PM

Each entry shows the completed timestamp. Devon taps one of the sessions to see more detail (optional; depends on his curiosity). The detail view shows:
- Completed at: 9:15 AM
- Duration: 25 minutes
- Break taken after: 5 minutes

Devon scrolls through the list and is satisfied. He switches to "This Week" and sees a bar chart showing sessions per day. Monday: 6, Tuesday: 5, Wednesday: 4 (a lighter day), Thursday: 6, Friday: 3 (incomplete). The chart makes it easy to spot patterns.

He taps on Wednesday (the 4-session day) and sees the sessions for that day. He notices: "Hmm, I had a lot of meetings on Wednesday. That explains the lower count. But I didn't expect Friday to drop to 3."

**Observable User States the Frontend Must Handle:**

- `idle` — Main screen showing summary counts (today, this week, all-time)
- `loading` — Fetching session data from backend (spinner on summary while waiting)
- `today_view` — List of today's sessions with timestamps and durations
- `today_empty` — No sessions completed today yet; show motivational message ("Start your first session!") and a prompt to begin
- `week_view` — Bar chart or table of sessions per day this week
- `alltime_view` — Line graph or summary of sessions across the entire history
- `detail_view` — Details of a single session (on tap)
- `offline` — No network; show cached data from the last sync, with a "Last updated: [timestamp]" note
- `error` — Backend failed to return history; show error message and a "Retry" button
- `stale` — Data is older than expected (last update > 5 minutes ago); show a "Refresh" button

**Frontend Responsibilities:**

1. On app open, fetch GET /sessions/today and GET /sessions/summary
2. Display the summary counts prominently (today, this week, all-time)
3. Support tabs or navigation: Today, This Week, All-Time
4. On "Today" tap, fetch GET /sessions/today and display the list
5. On "This Week" tap, fetch GET /sessions/week and display a chart
6. On "All-Time" tap, fetch GET /sessions/all-time and display a chart (or paginate if data is large)
7. Allow tapping a session to see details (show timestamps, durations, break status)
8. Cache the most recent response so offline users see stale-but-useful data
9. Show timestamps in the user's local time (convert from UTC if needed)
10. Handle pagination for large history (cursor-based, not offset-limit)
11. Show a "Refresh" button if data is > 5 minutes old

**Frontend-Backend Contract Points Exercised:**

- GET /sessions/today returns a list of sessions for the UTC-midnight-to-midnight range that aligns with the user's local midnight
- GET /sessions/week returns sessions for the last 7 days (inclusive boundaries)
- GET /sessions/all-time returns all sessions or paginated sessions with a cursor
- Summary counts (today, week, all-time) are accurate and include only completed sessions
- Timestamps are in ISO 8601 UTC format; frontend converts to local time for display
- Pagination uses cursor-based tokens, not offset-limit (for robustness to concurrent inserts)

**Failure Modes the Frontend Must Gracefully Handle:**

- Backend returns 400 on date-range query → show error message and a "Retry" button
- Backend returns 500 → show "Service temporarily unavailable" and suggest checking back later
- Network is slow → show a spinner on the summary counts while waiting
- Network drops mid-fetch → show cached data with "Last updated: [time] — offline" and a "Retry" button
- User's timezone changes (phone setting) → refresh the data and recalculate local timestamps
- Session count is 0 for the day → show an encouraging message ("No sessions yet! Start one now.") instead of an empty list
- History query returns sessions for the wrong day → debug: check timezone handling and UTC boundary assumptions
- Pagination cursor becomes invalid (data was purged) → reset to the first page

**Expected Outcome:**

Devon gets an instant, accurate snapshot of his daily productivity. The summary is visible at a glance; deeper views (week, all-time, single session) are accessible with one tap. The number he sees is the truth, and he can rely on it for his end-of-day reflection.

**When This Test Passes:**

The frontend successfully:
- Fetches and displays accurate session counts and history
- Shows data in a clear, scannable format (counts on main screen, charts on detailed views)
- Converts server timestamps to the user's local time correctly
- Handles offline scenarios by showing cached data
- Supports pagination for large histories
- Displays no count or empty-state message when there are no sessions
- Refreshes data on demand and shows freshness indicators
