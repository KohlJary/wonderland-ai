## Ticket 004: Implement break flow (auto-transition from session complete to break, display break timer)

**Sources:** take-a-structured-break
**Owner:** Tweedledee & Tweedledum (joint handoff)
**Tier:** v1
**Estimate:** 0.5–1 day, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: implement-session-state-backend, implement-session-timer-ui
- Soft: —

**Description:**

When a session completes, automatically start a 5-minute break (backend initiates transition, frontend displays break timer). Break timer is the same UI as session timer (just labeled "Break"). When break completes, return to idle state and allow user to start a new session. No customizable break length in v1 (hard-coded 5 min); no 'skip break' button.

**Acceptance:**
- On session complete, backend auto-transitions to 'break' state
- Frontend detects break state and displays break timer (MM:SS, starting at 05:00)
- Break timer counts down; on break complete (elapsed ≥ 5 min), backend transitions to 'idle'
- Frontend returns to idle state ready for new session start
- E2E: start session, let it complete, verify break timer appears, let break complete, verify idle state

**Risk:**

If the auto-transition logic lives on the backend, frontend must poll or listen for state changes. Clarify handoff in the contract document.
