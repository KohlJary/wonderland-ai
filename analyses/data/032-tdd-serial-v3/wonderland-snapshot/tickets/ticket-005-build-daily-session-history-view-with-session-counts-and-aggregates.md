## Ticket 005: Build daily session history view with session counts and aggregates

**Sources:** daily-review-of-session-history
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–2 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: log-completed-sessions-to-persistent-history
- Soft: —

**Description:**

Render a page showing today's sessions: count of completed focus sessions, total focus time, count of breaks, total break time. Show session list with timestamps. Do not include week/month aggregates or charts yet.

**Acceptance:**
- Daily view displays count of completed focus sessions today
- Daily view displays total minutes spent in focus sessions
- Daily view displays count of completed breaks
- Daily view shows individual session entries with start time, duration, type
- View updates when user completes a new session (without page refresh)

**Risk:**

Real-time update mechanism (polling vs. event-driven) not yet specified — may add 0.5 days depending on architecture choice.
