## Ticket 002: Frontend: session start button and timer display

**Sources:** start-and-complete-a-focus-session
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: session-ui-complete-button
- Blocked by: session-state-machine
- Soft: —

**Description:**

Build the UI for starting a session. Show a button labeled 'Start Focus Session'. On click, call the backend to transition state. Display a timer counting up from zero, updating every second. Show the target duration (e.g., '25 min') as reference. Disable the start button while a session is active.

**Acceptance:**
- Start button is visible and clickable when no session is active
- Timer appears and counts up after session starts
- Start button disables while session is active
- Timer stops when session is marked complete on the backend

**Risk:**

Timer accuracy depends on client-side clock; if backend and client drift, the UX will feel broken. Use server-provided elapsed time on fetch if possible.
