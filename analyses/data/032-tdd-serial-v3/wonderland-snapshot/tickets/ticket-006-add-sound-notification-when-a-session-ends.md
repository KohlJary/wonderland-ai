## Ticket 006: Add sound notification when a session ends

**Sources:** sound-notification-at-session-end
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5–1 day, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: focus-session-with-visual-countdown
- Soft: —

**Description:**

When a focus or break session timer reaches 0, play a short audio cue. Let user mute audio if desired (checkbox in settings). Audio file should be included in the app bundle.

**Acceptance:**
- A sound plays when focus session completes
- A sound plays when break session completes
- User can disable sound notifications in settings
- Mute preference is remembered across app launches

**Risk:**

Browser audio API permissions on some platforms may complicate testing; allocate 0.25 days for platform-specific debugging if needed.
