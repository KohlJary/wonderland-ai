## Implementation 002: History query endpoints and session aggregation

**Side:** backend
**Ticket:** feature-002
**Contract:** history-query-shape-and-windowing v1 (agreed M3)
**Ready for review:** no

**Approach:**

GET /sessions/history with optional ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD returns paginated list of completed sessions for user. Aggregates (total_focus_time, total_break_time, session_count) per day and per week. Windowing respects user's timezone (from settings or UTC default).

**Files:**
- src/backend/api/sessions.py: GET /sessions/history endpoint with window logic
- src/backend/models.py: aggregation helpers (sessions_by_day, sessions_by_week)

**Open Questions for Pair:**
- Frontend timezone handling: does client send timezone in query string, or do we read from user settings and use that?
- Pagination: page size 20, 50, or 100 sessions per response? Frontend has space constraints?

**Known Limitations:**
- Aggregation is computed per-request (no caching); acceptable for MVP but will need materialization if query volume scales
- Timezone logic currently defaults to UTC; needs integration with settings endpoint
