## Ticket 012: Implement session and break duration customization UI

**Sources:** customize-session-and-break-lengths
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.75–1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: session-preferences-backend

**Description:**

Build a settings panel where the user can set custom durations for focus sessions and breaks. Provide input fields with sensible defaults (e.g., 25 min sessions, 5 min breaks). Allow the user to save and apply these defaults. The customization should take effect on the next session start.

**Acceptance:**
- User can input a custom session duration
- User can input a custom break duration
- Settings are saved when the user clicks Save
- Saved settings are loaded when the app starts
- Input validation prevents nonsensical values (e.g., 0 min, negative durations)

**Risk:**

Deciding on min/max bounds for durations; clarify whether the app should allow very long sessions (e.g., 8-hour focus blocks).
