## Ticket 009: Data persistence across app restarts

**Sources:** story:trust-that-data-persists-across-app-restarts
**Owner:** tweedledee, tweedledum (pair acceptance test)
**Tier:** v1
**Estimate:** 0.5 days, 85% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket:timer-state-machine-and-session-lifecycle, ticket:history-append-only-log-and-session-aggregation, ticket:settings-read-and-write-endpoints, ticket:frontend-timer-ui-and-session-rendering, ticket:frontend-history-views-today-week-all-time, ticket:frontend-settings-ui
- Soft: —

**Description:**

Integration test: start a session, close app, reopen app, verify session is still running with correct countdown. Complete a session, close app, reopen app, verify session appears in history and new session starts fresh. Settings change persists.

**Acceptance:**
- Start session, kill app, restart: session countdown resumes from correct elapsed time
- Complete session, kill app, restart: session appears in history; timer is idle
- Change settings, kill app, restart: new timer uses updated lengths
- Test on both Android and iOS (or target platform)

**Risk:**

Low if Timer and History endpoints are solid. High if there's a clock-skew issue between client and server — mitigate by using server time from GET /session response.
