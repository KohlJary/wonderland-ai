## Ticket 003: Build break timer UI and lifecycle

**Sources:** take-a-break-and-return-to-work
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.75-1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: return-to-work-prompt
- Blocked by: start-run-session
- Soft: custom-duration-settings

**Description:**

Implement the break-session UI: after a focus session ends, prompt the user with a customizable break timer (default 5 min). Show running timer, allow skip/extend/complete. Coordinate with backend so break end triggers return-to-work prompt. Reuse timer display patterns from focus session UI to minimize duplication.

**Acceptance:**
- Break prompt appears after focus session completes
- Break timer runs with customizable duration
- User can skip, extend, or complete the break
- Break record persists in history

**Risk:**

Low risk; reuses timer patterns from focus session work.
