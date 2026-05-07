## Ticket 002: Implement customizable session and break lengths (settings panel)

**Sources:** customize-session-and-break-lengths
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: wire-settings-to-persistence
- Blocked by: implement-pomodoro-timer-ui-and-state-machine
- Soft: —

**Description:**

Add a settings/gear icon. When clicked, show a modal or panel with inputs for session length (default 25 min) and break length (default 5 min). Allow user to save custom values. Store in localStorage for now (no backend call yet). When user returns to the app, use the saved lengths for new sessions.

**Acceptance:**
- User can open a settings panel
- User can change session length and break length
- Custom lengths persist across page refresh (localStorage)
- Next session created after settings change uses the new lengths
- Settings panel can be dismissed without saving (changes not applied)

**Risk:**

None identified.
