## Ticket 004: Add session history view (today's session count)

**Sources:** review-today-s-session-count
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5–1 day, 75% confident
**Status:** open

**Dependencies:**
- Blocks: add-weekly-and-all-time-history-view
- Blocked by: wire-timer-state-to-backend-persistence
- Soft: —

**Description:**

Display today's completed session count prominently in the UI (e.g., 'Sessions today: 3'). Fetch the count from the backend or calculate from localStorage. Update in real-time when a session completes. Keep the visual simple and glanceable — the user should see at a glance how many focus blocks they've completed today.

**Acceptance:**
- Today's session count is displayed on the main screen
- Count updates immediately when a session completes
- Count resets at midnight (or on app load after midnight)

**Risk:**

Timezone handling: defer to fast-follow if complexity arises. Use server time for now.
