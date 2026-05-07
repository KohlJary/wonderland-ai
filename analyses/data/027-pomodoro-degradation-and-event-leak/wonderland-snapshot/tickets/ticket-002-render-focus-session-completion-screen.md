## Ticket 002: Render focus session completion screen

**Sources:** start-and-complete-a-focus-session, take-a-break-and-return-to-focus
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5-1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: persist-focus-session-to-indexeddb
- Blocked by: initialize-focus-session-with-user-set-duration
- Soft: —

**Description:**

When timer reaches 00:00, render a completion screen. Display: session duration, timestamp of completion, one-tap 'Mark Complete' button, one-tap 'Extend Session' button, one-tap 'Take a Break' button. No server calls in M1; all state is local.

**Acceptance:**
- Completion screen appears immediately when timer reaches 00:00
- 'Mark Complete' button writes completion status to local storage
- 'Extend Session' button returns to active timer with a new duration
- 'Take a Break' button shows break configuration screen

**Risk:**

Three-button UX could be confusing on mobile. Recommend A/B testing if time allows; MVP can start with 'Mark Complete' only.
