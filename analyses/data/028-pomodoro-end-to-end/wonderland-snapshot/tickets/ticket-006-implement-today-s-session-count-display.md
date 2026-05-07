## Ticket 006: Implement today's session count display

**Sources:** review-today-s-session-count-and-recent-activity
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: session-history-query
- Soft: —

**Description:**

Display a simple counter showing how many sessions the user has completed today. This should update in real time when a session completes. Show the count prominently on the main screen—it gives the user immediate feedback on their progress and is motivational.

**Acceptance:**
- Counter is visible on the main screen
- Counter displays the correct number of sessions completed today
- Counter updates immediately when a session completes
- Counter resets to 0 at midnight or at the start of a new day

**Risk:**

Timezone edge cases if the user's local midnight differs from server midnight; clarify which timezone is authoritative.
