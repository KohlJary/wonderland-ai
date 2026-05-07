## Story 008: Maya reviews the four sessions she completed today and sees their aggregate duration

**Persona:** Maya, 28, product manager, runs multiple short sessions throughout the day and wants to know at the end of the day whether she had enough focus time. She checks the timer app during breaks.

**Situation:**

It's 5 PM. Maya has run the pomodoro timer four times today (25 min, 25 min, 22 min, 25 min — one session was cut short by a meeting). She opens the 'Today' view to see how much focused time she actually got.

**Need:**

As Maya, I want to see a summary of all my completed sessions today and their total duration, so that I can gauge whether I had enough deep work time.

**Acceptance:**
- The 'Today' view displays a list of completed sessions (timestamp, duration for each).
- A total duration for the day is displayed prominently (e.g., 'Total focus time today: 1 hour 37 minutes').
- Sessions appear in reverse-chronological order (most recent first).
- The view updates immediately when a session completes (no page refresh required).

**Tier:** core

**Confusion-flags:**
- Does 'timestamp' mean the wall-clock time the session started, or the relative time ('2 hours ago')? Both are useful; the acceptance criterion doesn't say which.
- Should the total highlight whether Maya hit some implicit daily goal (e.g., a 'recommended' amount)? The feature claim doesn't mention goals, so probably not — but the absence is worth noting.
- Is the 'Today' view a separate tab/page, or a collapsible section on the main timer screen? The feature scope doesn't specify layout.
- What happens when Maya looks at the view just after midnight? Does 'today' reset automatically, or does she see both days until she manually clears yesterday's sessions?
