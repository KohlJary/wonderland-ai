## Story 005: Adjust focus and break session lengths

**Persona:** James, 42, a manager who is experimenting with work rhythms. James has read about Poisson distribution and wants to try 20-minute focus with 10-minute breaks instead of the standard 25/5 split.

**Situation:**

James opened the app and wants to customize it for his rhythm. He needs a settings view where he can change the focus duration and break duration.

**Need:**

As James, I want to adjust the focus session length and break length in settings, so that I can tailor the pomodoro rhythm to my own work style.

**Acceptance:**
- A Settings view is accessible from the main screen
- I can adjust 'Focus Duration' (default 25 min) to any value
- I can adjust 'Break Duration' (default 5 min) to any value
- When I start a new session after changing settings, it uses the new values

**Tier:** core

**Confusion-flags:**
- What are the bounds? Can James set a 1-minute focus session? A 180-minute one? Should there be validation or warnings?
- Should changing settings affect an *in-progress* session, or only new sessions? This feels like it matters and I can't tell.
