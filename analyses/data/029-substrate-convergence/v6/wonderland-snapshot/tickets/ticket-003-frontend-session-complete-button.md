## Ticket 003: Frontend: session complete button

**Sources:** start-and-complete-a-focus-session
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: session-review-query
- Blocked by: session-ui-start-button
- Soft: —

**Description:**

Build a 'Complete Session' button visible only when a session is active. On click, call the backend to end the session. Disable the button immediately after click (prevent double-submission). Update the timer to show final duration instead of continuing to count.

**Acceptance:**
- Complete button appears only when session is active
- Clicking complete calls backend and transitions state
- Button is disabled immediately to prevent race conditions
- Timer freezes to show final duration

**Risk:**

Network latency on the complete call could leave the button disabled indefinitely if the response doesn't arrive. Implement a timeout and a retry.
