## Ticket 004: Session persistence: read/write focus and break sessions to disk

**Sources:** persistent-settings
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1–1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: daily-session-log-backend, settings-backend
- Blocked by: —
- Soft: core-timer-state-machine, break-timer-state-machine

**Description:**

Storage layer (file-based or embedded DB, choice TBD with architecture). Save and restore the full state of both the focus session and break session machines. Scope: single-user, single-device. No sync, no multi-device, no cloud. Just local durability. API: given a session ID, load its state; given state mutations, persist them.

**Acceptance:**
- Start a focus session, close the app, reopen: session state is intact
- Start a break, pause it, restart the app: break state resumes from paused value
- Multiple sessions are stored and retrievable by ID

**Risk:**

Storage choice (SQLite vs. file-based JSON) will affect this ticket's complexity. Architect a simple boundary so the state machines don't care. Expand estimate to 2 days if we choose SQLite and need migrations.
