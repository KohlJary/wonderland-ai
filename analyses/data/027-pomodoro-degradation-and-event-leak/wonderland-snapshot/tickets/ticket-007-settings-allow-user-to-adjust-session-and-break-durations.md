## Ticket 007: Settings: allow user to adjust session and break durations

**Sources:** adjust-focus-and-break-session-lengths
**Owner:** tweedledee
**Tier:** fast-follow
**Estimate:** 1-1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: initialize-focus-session-with-user-set-duration

**Description:**

User can navigate to a Settings screen where they can update default focus session duration and default break duration. Presets are configurable (e.g., user can change 25 to 20, add 35 to presets, etc.). Settings are persisted to local storage and used as defaults in future sessions.

**Acceptance:**
- Settings screen is accessible from home screen or within a session
- User can edit preset durations and custom defaults
- Changes are persisted to local storage
- New sessions use updated defaults

**Risk:**

Low.
