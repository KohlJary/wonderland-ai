## Ticket 004: History append-only log and session aggregation (backend)

**Sources:** story:review-today-s-session-count, story:review-weekly-and-all-time-history
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1–1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: ticket:frontend-history-views-today-week-all-time
- Blocked by: ticket:define-session-state-machine-and-contract-for-timer-history-seam, ticket:schema-and-migrations-for-timer-and-history, ticket:timer-state-machine-and-session-lifecycle
- Soft: —

**Description:**

Endpoints: GET /history/today (sum completed sessions, count, avg duration), GET /history/week (same, last 7 days), GET /history/all-time (cumulative). Each endpoint reads from session_history, aggregates, returns. No writes except session completion (handled by Timer). Design for append-only semantics: once a session_history row is written, it is never updated or deleted.

**Acceptance:**
- GET /history/today returns { sessions_count, total_focus_duration, total_break_duration, avg_session_length }
- GET /history/week returns same fields, filtered to last 7 calendar days
- GET /history/all-time returns same fields, cumulative
- Queries use indexes on session_history.completed_at for performance
- Endpoint is read-only; no POST/PATCH on /history

**Risk:**

Query performance on large history tables (months of data). Mitigate with indexes; if performance becomes issue, add caching layer in fast-follow.
