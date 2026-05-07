## Ticket 004: Implement web notifications for session end

**Sources:** start-and-complete-a-focus-session
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5-1 day, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: session-state-machine
- Soft: —

**Description:**

When a focus session or break ends, fire a web notification. Handle the case where the user has denied notification permission (graceful fallback — maybe a visual alert in-tab). Do not implement background worker / service worker in v1; web notifications are synchronous and tied to the tab being open. If the user closes the tab, they don't get the notification — that's v1 scope.

**Acceptance:**
- Notification fires at end of session
- Permission request handled gracefully
- Fallback UI alert shows if permission denied
- Notification text is clear and actionable

**Risk:**

Notification permission state is persistent; may need to guide user to re-enable if they denied. Mitigation: detect denial and offer gentle in-app re-prompt.
