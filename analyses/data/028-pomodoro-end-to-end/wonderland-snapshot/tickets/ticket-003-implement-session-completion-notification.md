## Ticket 003: Implement session completion notification

**Sources:** start-a-focus-session-and-receive-completion-notification
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5–1 day, 75% confident
**Status:** open

**Dependencies:**
- Blocks: session-break-ui
- Blocked by: session-timer-backend
- Soft: —

**Description:**

When a session completes (backend timer elapses or user explicitly ends it), display a prominent notification to the user confirming the session ended and the time logged. The notification should be dismissible and should not block further interaction. No sound or vibration yet—visual notification only.

**Acceptance:**
- Notification appears when session timer completes
- Notification displays session duration and completion time
- User can dismiss the notification
- Notification does not prevent the user from starting a new session immediately after

**Risk:**

Notification timing race if backend completion event arrives after frontend timer hits zero; add a small grace period or reconcile on poll.
