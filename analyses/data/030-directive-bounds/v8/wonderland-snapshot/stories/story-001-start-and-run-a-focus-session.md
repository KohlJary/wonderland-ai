## Story 001: Start and run a focus session

**Persona:** Marcus, 34, software engineer, uses pomodoro to protect deep work from Slack interruptions. He has tried five timer apps and keeps abandoning them because they feel like overhead rather than help.

**Situation:**

Marcus is about to start a task that requires sustained focus. He wants to mark the boundary between 'focused work' and 'available for interruption' in a way that is visible to him and, eventually, to his team calendar.

**Need:**

As Marcus, I want to start a 25-minute focus session with a single tap and receive a clear notification when it ends, so that I can trust the timer and stop checking the clock.

**Acceptance:**
- One tap starts a session; the app displays remaining time visibly during the session.
- The notification when time expires is unmissable (sound + visual, or both configurable).
- I can dismiss the notification and immediately start a break without extra steps.
- If I close the app during a session, the timer keeps running and notifies me anyway.

**Tier:** core

**Confusion-flags:**
- I'm not sure whether the timer should keep running if the phone locks or goes to sleep. For Marcus, yes — the discipline is the point. But some users might want to pause. This feels like a settings question, not a core experience question.
- The 'notification' is doing a lot of work here. Is it a system notification, an in-app alert, vibration? The answer changes the UX significantly. Leaving this to the team, but marking it as a real decision point.
