## Story 006: Abandon a session without affecting history

**Persona:** Jordan, 29, a consultant who gets interrupted by meetings and urgent calls. Sometimes 10 minutes into a session, a meeting appears on the calendar. Jordan wants to stop the timer without the incomplete session cluttering their history.

**Situation:**

Jordan is 10 minutes into a session when a calendar alert pops. They need to stop the timer and attend the meeting. When they return, they want to start a fresh session without the incomplete one counting toward their daily total.

**Need:**

As Jordan, I want to stop a session mid-timer and discard it from my history, so that my counts reflect actual focus time, not interrupted attempts.

**Acceptance:**
- There is a visible 'stop' or 'abandon session' button during an active session
- Tapping it shows a confirmation ('This session will not be saved')
- The session is removed from the count; the history does not record it

**Tier:** enrichment

**Confusion-flags:**
- Should the user be able to abandon and re-do the same session (e.g., 'I did 10 minutes, can I save those 10 minutes and add them to a future session')? That is clever but complex. Probably v2.
- Is the abandon button always visible, or only when I tap a 'menu' on the timer? Always visible risks accidental abandons; hidden risks friction when needed.
