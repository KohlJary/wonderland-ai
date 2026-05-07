## Ticket 002: Implement session timer UI (start, pause, complete, display elapsed time)

**Sources:** start-and-complete-a-focus-session
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 1–1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: design-and-document-session-state-contract, implement-session-state-backend
- Soft: —

**Description:**

Frontend: render a timer display (MM:SS), buttons to start/pause/complete the session, and a label showing "Focus session" or "Break". On start, transition the session state (via backend call) to 'running'. On tick (every second), display elapsed time. On complete button, transition to 'complete'. Display is dumb; state is backend-owned. Hard stop: do not implement settings UI or session history in v1.

**Acceptance:**
- Timer displays MM:SS and updates every second while session is running
- Start button transitions session to running; Pause button transitions to paused; Complete button transitions to complete
- Visual indicator shows current mode (focus vs. break)
- E2E test: start a session, let it run 3 seconds, verify display shows elapsed time, complete it

**Risk:**

If the backend contract shifts after UI is built, UI rework is quick but annoying. Risk is low if contract is nailed first.
