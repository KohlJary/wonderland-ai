## Ticket 008: Build settings UI: adjust session and break durations

**Sources:** adjust-session-and-break-durations
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5-1 day, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: indexeddb-store
- Soft: —

**Description:**

Simple form: input fields for session duration (minutes) and break duration (minutes). Persist to a settings record in IndexedDB. Apply the settings to new sessions; don't retroactively change ongoing sessions. Keep it minimal: two inputs, a save button, maybe a 'restore defaults' button.

**Acceptance:**
- Settings form renders and accepts input
- Changes persist across page reload
- New sessions use the updated durations
- Defaults are sensible (25 min focus, 5 min break)

**Risk:**

None identified.
