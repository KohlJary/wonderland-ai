## Contract Note 006: Feature 003: Historical aggregations (weekly, all-time)

**State:** respond
**Contract Version:** (unlocked)

**Current Shape:**

Backend read-only endpoints: GET /api/session-history/weekly (returns completed sessions from past 7 days, grouped by day, with counts and durations), GET /api/session-history/all-time (same shape, unbounded).

**Your Questions (Tweedledum):**

1. **Response includes both counts and durations?** → Yes. Both required. Response shape (both endpoints):
```
{
  "period": "weekly" | "all-time",
  "data": [
    {
      "date": "2025-01-15",
      "session_count": 4,
      "total_focus_duration_minutes": 100,
      "break_duration_minutes": 20
    },
    ...
  ]
}
```
Frontend uses count + total_focus_duration for rendering; having both lets us add future visualizations (bar chart by duration, not just count) without schema change.

2. **Date format?** → ISO 8601 string ("2025-01-15"). Simpler than timestamp, unambiguous.

3. **Timezone handling?** → Known limitation for v1: backend calculates "past 7 days" in UTC. Frontend displays each day as-is (date string), so the user's local "today" might not align with UTC "today" if they're in a non-UTC timezone. This will be fixed in v1.1 when we add timezone awareness (frontend sends tz offset, backend calculates relative to user's local time). For now, document the limitation in the implementation artifact ("Historical dates use UTC, not local timezone").

4. **Pagination for all-time?** → No pagination for v1. Unbounded is fine for single-user. If data grows beyond reason later, add optional `&limit=90` parameter, but don't implement now. Document as "all-time returns all historical data (no pagination in v1)".

5. **Order of days?** → Newest-first (most recent date at index 0). Matches the typical mobile UX expectation (today at the top, scroll to see older data).

**Frontend Impact (Tweedledee):**

Frontend provides a history screen accessible from the main menu. Two tabs: `This Week` and `All Time`. Each tab renders a list of daily summaries.

Loading strategy:
- `This Week` tab: fetch on tab open (GET /api/session-history/weekly). Cache in-memory for duration of screen display. Auto-refresh every 5 minutes if tab is active (to show newly-completed sessions). On app return-to-foreground, refetch (in case the app was backgrounded for >5 min and new sessions completed).
- `All Time` tab: fetch on tab open (GET /api/session-history/all-time). Cache in-memory for the entire app session. Refetch only on app restart or if user explicitly pulls-to-refresh. (All-time changes slowly; no need for frequent refresh.)

UI rendering: each day is a row showing:
- Date (e.g., "Wed, Jan 15")
- Session count (e.g., "4 sessions")
- Visual indicator: color-coded productivity badge (0 sessions = gray, 1-2 = light green, 3+ = dark green) or simple text (e.g., "Good day!")
- Total focus time in parentheses (e.g., "4 sessions, 100 minutes")

Tapping a day: v1 does NOT expand to show individual session details. Just show the aggregate. Individual session details are post-v1.

UI states:
- `loading`: show skeleton rows (5-7 placeholder rows)
- `loaded`: render the day list
- `empty`: no sessions recorded, show "No sessions yet. Start your first session!"
- `error`: fetch failed, show error message + Retry button

Cache invalidation:
- Weekly: auto-refresh every 5 min while tab is open; refetch on app-return-to-foreground; reset on calendar day change (midnight). If app is open past midnight and the last session completed just before midnight, the weekly tab will show the session under today, but it might be in UTC "yesterday" — document as a limitation.
- All-time: no auto-refresh; user must pull-to-refresh or restart app.

**Backend Impact (Tweedledum):**

Two read-only endpoints. Response shape is identical for both; only the data range differs:
- GET /api/session-history/weekly: SessionRecord records where completed_at >= (today - 7 days) in UTC
- GET /api/session-history/all-time: all SessionRecord records, no date filter

Both return newest-first (ORDER BY completed_at DESC).

Schema: SessionRecord table (completed_at, session_duration_minutes, break_duration_minutes, session_type enum) with indexed completed_at.

Performance: weekly query hits completed_at index, efficient. All-time query is a full table scan, but v1 is single-user so not a concern yet. If this becomes slow at scale, add pagination.

**Resolution:**

Locked at:
- GET /api/session-history/weekly: past 7 days (UTC), newest-first
- GET /api/session-history/all-time: all history, newest-first
- Response: `{"period": "weekly"|"all-time", "data": [{"date": "2025-01-15", "session_count": 4, "total_focus_duration_minutes": 100, "break_duration_minutes": 20}, ...]}`
- Frontend: cache weekly for 5 min + auto-refresh + refetch on app-return; cache all-time once per session, user-driven refresh only
- Known limitations: timezone handling (UTC only), no pagination (v1 unbounded), no individual session drill-down (aggregate only)
