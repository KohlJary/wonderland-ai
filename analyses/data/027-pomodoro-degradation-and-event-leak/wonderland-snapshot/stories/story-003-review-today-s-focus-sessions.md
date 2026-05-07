## Story 003: Review today's focus sessions

**Persona:** Priya, 29, a product manager who tracks her own productivity as data. She wants to know: how many focus sessions did I complete today? Is that more or fewer than yesterday? She uses this to calibrate her own workload.

**Situation:**

Priya has done several pomodoro cycles throughout her day. Now (end of day, or mid-afternoon) she wants to see a summary: total sessions completed, total focus time, total breaks taken.

**Need:**

As Priya, I want to see a view of today's sessions at a glance — count, total time, sessions completed — so that I can track my own productivity and notice patterns.

**Acceptance:**
- There is a 'Today' or 'History' view accessible from the main screen
- This view shows: number of focus sessions completed today, total minutes in focus, number of breaks taken
- The data persists across app restarts (it is saved, not calculated in-memory)

**Tier:** core

**Confusion-flags:**
- Should incomplete sessions count (e.g., a session started but not finished)? Or only completed ones?
- The directive says 'today's count, this week, all-time' but I'm starting with today. I'm not sure if week/all-time views are core or enrichment.
