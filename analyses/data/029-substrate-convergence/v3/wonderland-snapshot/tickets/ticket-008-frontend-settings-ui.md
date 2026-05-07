## Ticket 008: Frontend settings UI

**Sources:** story:adjust-session-and-break-lengths
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.75–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket:settings-read-and-write-endpoints
- Soft: —

**Description:**

Settings screen: two inputs (session_length, break_length in minutes), defaults to 25/5. Save button calls PATCH /settings, shows confirmation, navigates back to timer. Settings persist (stored on backend); on app restart, frontend reads from GET /settings on startup.

**Acceptance:**
- Settings screen accessible from timer UI
- Session and break length inputs accept integers > 0
- Save button calls PATCH /settings and shows success confirmation
- App startup reads GET /settings and uses returned values for next timer session

**Risk:**

Low. Straightforward form.
