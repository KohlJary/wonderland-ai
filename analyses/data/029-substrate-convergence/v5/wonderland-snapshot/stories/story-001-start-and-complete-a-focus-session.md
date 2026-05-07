## Story 001: Start and complete a focus session

**Persona:** Marcus, 34, a software engineer who works from home and struggles with distraction. He uses timers to force himself to focus on hard problems without checking Slack.

**Situation:**

Marcus sits down to tackle a complex refactor. He knows if he doesn't constrain himself, he'll context-switch within 10 minutes. He opens the pomodoro tracker.

**Need:**

As Marcus, I want to start a 25-minute focus session with one click, so that I can stop negotiating with myself about when to look at my phone.

**Acceptance:**
- I tap 'Start Session' and a 25-minute timer begins immediately, showing time remaining
- The timer counts down visibly; I can see at a glance how much time is left
- When 25 minutes elapse, I receive a clear notification (sound, visual, or both) that the session is complete
- The session is automatically recorded to my history with the timestamp it occurred

**Tier:** core

**Confusion-flags:**
- What happens if I close the app during a session? Does the timer keep running, pause, or reset? The user's mental model matters here.
- Is the notification something I can dismiss and ignore, or does it demand attention? Depends on the user's environment (open office vs. home office vs. shared space).
- Can I see the timer while doing other tasks, or only if the app is in focus? This affects whether the app needs to live in a system tray or notification area.
