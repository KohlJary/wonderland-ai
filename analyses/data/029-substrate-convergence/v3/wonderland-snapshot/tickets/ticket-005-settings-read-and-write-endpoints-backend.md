## Ticket 005: Settings read and write endpoints (backend)

**Sources:** story:adjust-session-and-break-lengths
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.5 days, 85% confident
**Status:** open

**Dependencies:**
- Blocks: ticket:frontend-settings-ui
- Blocked by: ticket:schema-and-migrations-for-timer-and-history
- Soft: ticket:timer-state-machine-and-session-lifecycle

**Description:**

GET /settings returns current session_length and break_length (in minutes). PATCH /settings updates them. Timer state machine reads settings on /session POST (for countdown_ms calculation). No complex validation; just ensure lengths are > 0.

**Acceptance:**
- GET /settings returns { session_length: 25, break_length: 5 } (or user-set values)
- PATCH /settings ?session_length=30 &break_length=5 updates and returns new settings
- Settings persist across app restarts (read from database on startup)
- Validation: session_length and break_length must both be > 0 and < 600 (10 hours)

**Risk:**

Low. Straightforward CRUD.
