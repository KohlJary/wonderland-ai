## Contract Note 003: Today's Sessions Fetch Shape

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

(none yet — first draft)

**Proposed Change:**

GET /sessions/today — request has no body; response is {sessions: [{id, start_time, end_time, duration_seconds, is_completed}, ...], summary: {count, total_seconds}}. Ordered by start_time descending. Filter by current user, by created_at on today (server timezone-aware).

**Source:** story-003 (review-today-s-completed-sessions) + ticket-004 (backend-fetch-today-s-sessions-review-endpoint) + ticket-005 (frontend-today-s-sessions-review-card)

**Frontend Impact (Tweedledee):**

Frontend renders a list of sessions from response.sessions. Each row: start_time displayed as human time (e.g. "2:15 PM – 2:40 PM"), duration_seconds formatted as "25m 30s". UI state "empty" when sessions array is empty (show "No sessions completed today"). UI state "loading" while fetch is in flight. On success, transitions to "idle" (list displayed). Refresh behavior: fetch on mount. User can manually pull-to-refresh (or tap refresh button). Polling: do NOT implement polling for today's list — user taps refresh to see latest. Offline: cache last fetch result; show "offline" badge on stale data if offline for >1min. Response latency: should be <1s for UX (list feels responsive).

**Timing constraint:** If user just completed a session and navigates to review screen, they expect to see their completed session in the list immediately. Current backend filters by created_at on today, not by session start_time. Verify: does created_at match user's timezone? If backend uses UTC created_at but user is in PST, a session started at 11:50 PM PST (Dec 9) that completed after midnight (Dec 10) might not appear on "today" list if created_at is judged by UTC. Clarification needed.

**Backend Impact (Tweedledum):**

Query is SELECT * FROM sessions WHERE user_id=? AND DATE(created_at)=DATE(NOW()) ORDER BY start_time DESC. Return only is_completed=true sessions (active sessions don't show in history yet). Summary is computed server-side: count and sum of (end_time - start_time). Timezone: assume all times stored as UTC, 'today' is judged by server's configured timezone (to be surfaced in settings later, for now assume UTC). Invariant: every session returned is owned by the authenticated user. Response is always valid JSON even if empty (no sessions today).

---

**Open questions for pair:**

1. **Timezone handling:** If backend judges "today" by UTC but user is in different timezone, they might not see sessions they completed late in their local evening. Should we add a ?timezone query param, or store user timezone in user config? For v1, should we just document that "today" is UTC-based?

2. **Active sessions in today's list:** Backend filter is is_completed=true only. If user has an active session running, it won't appear in /sessions/today response. Frontend should fetch from elsewhere (maybe cache it in state from the start endpoint). Or should today's endpoint include {completed: [...], active: {...}}? Current shape assumes only completed; clarify if this is right.
