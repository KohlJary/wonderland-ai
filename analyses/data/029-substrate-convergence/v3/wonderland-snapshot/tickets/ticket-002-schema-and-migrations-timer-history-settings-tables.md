## Ticket 002: Schema and migrations: Timer, History, Settings tables

**Sources:** adr:separate-timer-history-and-settings-into-distinct-persistence-entities
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.5–0.75 days, 85% confident
**Status:** open

**Dependencies:**
- Blocks: ticket:timer-state-machine-and-session-lifecycle, ticket:history-append-only-log-and-session-aggregation, ticket:settings-read-and-write-endpoints
- Blocked by: ticket:define-session-state-machine-and-contract-for-timer-history-seam
- Soft: —

**Description:**

Create three tables per the ADR: sessions (timer state), session_history (append-only log), user_settings (config). Include created_at, updated_at on mutable tables; immutable marking on history. Migration reversible. No data, just schema.

**Acceptance:**
- Sessions table supports Timer state machine (see contract ticket)
- Session_history table is append-only, immutable once written
- User_settings table has session_length, break_length columns with defaults
- Migration file(s) present and testable in isolation
- Tweedledee has reviewed schema and signed off

**Risk:**

Tweedles disagree on column names or types — mitigated by contract ticket finishing first.
