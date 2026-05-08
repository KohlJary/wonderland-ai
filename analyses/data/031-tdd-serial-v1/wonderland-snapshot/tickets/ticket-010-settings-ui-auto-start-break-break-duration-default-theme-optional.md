## Ticket 010: Settings UI: auto-start break, break duration default, theme (optional)

**Sources:** persistent-settings
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.75–1.25 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: settings-backend
- Soft: —

**Description:**

A settings screen or modal where the user can configure app defaults. Auto-start break after a focus session completes (yes/no). Default break duration (5 min, 10 min, custom). Optional: theme (light/dark). Bind to the settings backend store. This is where persistent UI preferences live.

**Acceptance:**
- User opens Settings; sees toggle for auto-start break
- User can change default break duration
- User changes are persisted across app restarts
- Changed settings take effect on next session

**Risk:**

Low. Settings are stored, no complex logic.
