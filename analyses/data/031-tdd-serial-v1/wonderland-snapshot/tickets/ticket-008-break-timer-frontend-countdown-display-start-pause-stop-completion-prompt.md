## Ticket 008: Break timer frontend: countdown display, start/pause/stop, completion prompt

**Sources:** break-timer-between-sessions
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: break-complete-notification
- Blocked by: break-timer-state-machine
- Soft: —

**Description:**

User-facing UI for break time. After a focus session completes, the break timer screen appears (optionally auto-start, configurable in settings). Display remaining break time as a countdown. Buttons: Start (if not running), Pause, Stop. When the break countdown reaches zero, notify the user (visual, audio, or modal) that break time is done. Bind to the backend break state machine.

**Acceptance:**
- User starts a break; timer counts down on-screen
- Pause/resume work
- When timer reaches 0:00, user is notified
- User can dismiss notification and start a new focus session

**Risk:**

Notification delivery (browser notifications, audio, visual cue). For v1, use a simple modal. Add audio and browser notifications in fast-follow if the persona values ambient cues.
