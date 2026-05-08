## Ticket 001: Implement focus/break session timer UI with visual countdown

**Sources:** focus-session-with-visual-countdown, visual-distinction-between-focus-and-break
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1.5–2.5 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: sound-notification-at-session-end, persistent-settings-across-app-launches
- Blocked by: —
- Soft: —

**Description:**

Build the core timer display component showing elapsed and remaining time for focus and break sessions. Implement visual countdown (text + progress indicator). Accept start/pause/resume/skip controls. Distinguish visually between focus (e.g., blue) and break (e.g., green) states. Do not persist state yet; do not add sound yet.

**Acceptance:**
- Timer displays elapsed time and remaining time during a 25-minute focus session
- Progress bar or visual indicator fills as session progresses
- Visual styling clearly distinguishes focus (primary color) from break (secondary color)
- User can pause, resume, and skip to the next session
- Timer counts down visibly in real time

**Risk:**

If visual distinction requirement conflicts with accessibility (contrast, colorblind users), may need design iteration — allocate +0.5 days.
