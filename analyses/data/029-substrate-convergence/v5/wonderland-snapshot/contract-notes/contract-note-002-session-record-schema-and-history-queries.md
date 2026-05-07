## Contract Note 002: Session record schema and history queries

**State:** agreed
**Contract Version:** v1 (GET /api/sessions/today, /api/sessions?from_date=...&to_date=...&limit=50&offset=0, /api/sessions/stats?period=week|all_time. Queries return session records: {id, started_at, completed_at, duration_seconds, completed_break_at}. Cursor-based pagination with opaque next_cursor tokens. UTC midnight boundaries on backend.)

**Current Shape:**

undefined

**Proposed Change:**

Persisted session record contains: id (uuid), user_id (fk), created_at (timestamp when recorded), started_at (timestamp user clicked start), completed_at (timestamp user received 'done' notification), duration_seconds (the configured session length), completed_break_at (nullable timestamp when user completed the following break, if any). GET /sessions (query params: from_date, to_date, optional limit=50) returns array of session records in descending order by started_at. GET /sessions/today returns sessions where started_at is within calendar day (user's local midnight, negotiable). GET /sessions/stats?period=week|all_time returns {total_sessions, avg_sessions_per_day, sessions_per_day: [{date, count}, ...]}.

**Source:** Stories 003-004 (history views) and feature 003

**Frontend Impact (Tweedledee):**

Your assessment of date filtering and pagination UX.

**Backend Impact (Tweedledum):**

History queries filter by UTC midnight boundaries (full calendar days); cursor-based pagination with opaque next_cursor tokens (session_id + created_at encoded). Race window: new sessions can arrive while client pages — cursor approach handles monotonic ordering without requiring snapshot semantics.

**Resolution:**

Frontend handles date normalization (local midnight), backend filters by UTC boundaries. Cursor pagination eliminates race-window issues. Supports calendar views, date-range filters, and statistics aggregation.
