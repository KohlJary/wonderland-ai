## Ticket 005: Break session: user-set duration and return-to-focus flow

**Sources:** take-a-break-and-return-to-focus
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1-1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: persist-focus-session-to-indexeddb
- Blocked by: render-focus-session-completion-screen
- Soft: —

**Description:**

When user selects 'Take a Break', show a break configuration screen (presets: 5, 10, 15 min + custom). User sets break duration. Timer counts down. When timer reaches 00:00, show 'Return to Focus' button (which initiates a new focus session, using the original duration or asking for a new one). Break sessions are logged to IndexedDB but are distinct from focus sessions.

**Acceptance:**
- Break configuration screen appears when user selects 'Take a Break'
- Break timer counts down accurately
- 'Return to Focus' button appears and initiates a new focus session
- Break records (start, duration, completion) are stored in IndexedDB

**Risk:**

UX for 'return to focus' could be ambiguous (same duration? ask again?). Recommend: ask user to confirm duration on return.
