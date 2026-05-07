## Story 002: Take a break and return to work

**Persona:** Priya, 28, product manager, uses pomodoro to batch context-switching. She does four focused sessions in a row, then takes a longer break. She wants the break timer to feel distinct from work time — a permission to step away, not a countdown back to work.

**Situation:**

Priya has just received the notification that her 25-minute session is complete. She wants the app to acknowledge the work is done and give her explicit permission to actually stop thinking about the task.

**Need:**

As Priya, I want a clear break timer to start automatically after a session ends, so that I feel the transition from 'working' to 'resting' and actually rest instead of jumping into the next task.

**Acceptance:**
- After session notification, tapping 'take break' starts a 5-minute break timer (or custom break length if configured).
- The break timer has a visibly different UI from the work timer (color, tone, anything that signals 'you are not working now').
- When the break ends, I get a gentle notification (quieter than work-session notification) that break is complete.

**Tier:** core

**Confusion-flags:**
- Is the break timer mandatory, or can you skip it? Pomodoro purists say mandatory; but actual users often skip breaks. Leaving this as a design choice.
- The 'different UI' for break time — I don't want to overspecify, but the UX distinction here feels load-bearing. The team will know better how to signal this than I do.
