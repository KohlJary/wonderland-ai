## Ticket 006: Implement custom session and break duration settings

**Sources:** customize-session-and-break-lengths
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.75-1.25 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: persistent-storage
- Soft: start-run-session

**Description:**

Build settings UI: allow user to set default focus session length and break length (e.g., 25 min focus / 5 min break, or custom). Store in persistent storage, apply as defaults on new session creation. UI should be simple: two sliders or number inputs, with presets (Pomodoro standard: 25/5, or custom). No complex logic; just storage and application of user preference.

**Acceptance:**
- User can set custom focus session duration
- User can set custom break duration
- Settings persist across app restarts
- New sessions use the custom durations by default
- Presets are available (standard Pomodoro, custom range)

**Risk:**

Low. State management and persistence only.
