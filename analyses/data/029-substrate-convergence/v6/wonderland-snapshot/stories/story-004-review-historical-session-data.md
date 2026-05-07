## Story 004: Review historical session data

**Persona:** Priya, 31, a program manager who believes in data-driven self-improvement. She wants to see whether her pomodoro discipline has improved over weeks, and she wants to be able to spot patterns (do Fridays feel less focused than Mondays).

**Situation:**

Priya opens the app and taps to the history screen. She wants to see this week's count, compare it to last week, and see her all-time sessions.

**Need:**

As Priya, I want to see how many sessions I completed today, this week, and all-time, organized clearly enough that I can spot my patterns, so that I can adjust my schedule or goals if the data suggests I should.

**Acceptance:**
- The history screen shows three summary rows: today's count, this week's count, all-time count (each is a single number, e.g., '8 sessions')
- I can tap each row to expand and see more detail (date-by-date breakdown, longest streak, average sessions per day)
- The data loads fast and does not feel like I am waiting for a server

**Tier:** core

**Confusion-flags:**
- How far back do we go with 'all-time'? If Priya used the app for a year, showing every single day might be overwhelming. Do we aggregate by week or month? Or do we show a graph? This is a visualization question we haven't answered.
- What is the difference between 'this week' and a rolling 7 days? Monday start vs. rolling matters for some users. We should decide and be explicit.
