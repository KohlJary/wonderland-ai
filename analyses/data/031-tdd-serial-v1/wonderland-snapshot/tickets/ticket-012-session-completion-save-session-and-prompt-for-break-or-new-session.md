## Ticket 012: Session completion: save session and prompt for break or new session

**Sources:** focus-session-timer, break-timer-between-sessions
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.75–1.25 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: focus-session-frontend
- Soft: session-persistence-backend

**Description:**

When a focus session is stopped, the frontend prompts the user: Save and Start Break / Save and Discard / Discard Without Saving. If the user chooses Save and Start Break, the break timer screen appears. If Save and Discard, return to the main screen. Coordinate with backend to ensure session is persisted before showing the prompt.

**Acceptance:**
- User stops a focus session; prompted with three options
- If user chooses Save and Break, session is saved and break timer starts
- If user chooses Save and Discard, session is saved and UI returns to start screen
- If user chooses Discard, the session is not saved

**Risk:**

Race condition if the user tries to navigate away before the save completes. Add a loading state and disable navigation until the save is done.
