## Test Scenario: Priya Reviews Historical Session Data

**Severity:** breakage (if this fails, Priya can't track her patterns)

**Setup:**

Priya is a 31-year-old program manager who believes in data-driven self-improvement. She has been using the app for 3 weeks. She wants to see whether her focus discipline is improving. She opens the history screen.

**Trigger:**

Priya navigates to the history or stats view. She expects to see three summary rows: today's count, this week's count, and all-time count. She taps on "this week" to see a breakdown by day.

**Expected:**

1. GET /sessions/history (or similar) returns three summaries:
   - today: count and total_seconds for sessions created today
   - this_week: count and total_seconds for sessions created in the current week (Monday–Sunday or rolling 7 days)
   - all_time: count and total_seconds for all sessions ever created by the user
2. Each summary is a simple object with count (integer) and total_seconds (number)
3. Optional: GET /sessions/history?expand=all or similar provides day-by-day breakdown
4. GET /sessions/range?start_date=2024-01-01&end_date=2024-01-31 returns sessions within that date range
5. Response timestamps are consistent (all ISO8601) and correctly filtered by date

**Concern:**

The concern is that:
- Week boundaries might be inconsistent (Monday vs. rolling 7 days)
- Date filtering might not respect timezones (session at 11:59 PM in user's timezone might appear on wrong day)
- Large result sets (365+ sessions for all-time) might cause performance issues without pagination
- Date range queries might fail with invalid date formats or reversed boundaries
- The word "today" and "this week" might be ambiguous in multi-timezone scenarios

**Property:**

For all users U:
- GET /sessions/history returns summaries where all counts >= 0
- all_time.count >= this_week.count >= today.count (monotonic inclusion)
- GET /sessions/range with valid start_date and end_date returns all sessions S where created_at is within the range
- All timestamps are ISO8601 strings

**Implies:**

- Implies GET /sessions/history endpoint (or /sessions/stats)
- Implies GET /sessions/range endpoint with date-range query parameters
- Implies consistent timezone handling for date boundaries
- Implies pagination or result-size limits for large queries
