## Story 005: Adjust session and break durations

**Persona:** Chen, 31, a designer who experiments with different Pomodoro intervals (sometimes 30 minutes, sometimes 15, depending on the task).

**Situation:**

Chen is starting a new project with shorter, intense focus bursts. He opens settings and wants to change his session length from 25 to 15 minutes.

**Need:**

As Chen, I want to change my default session and break lengths in settings, so that I can adapt the method to the kind of work I'm doing today.

**Acceptance:**
- Settings are accessible from the main view (menu, gear icon, or dedicated tab)
- Session length and break length are independently adjustable (in minutes)
- New sessions created after a settings change use the new durations
- The settings are saved persistently (survive app close and reopen)

**Tier:** core

**Confusion-flags:**
- Does Chen's change apply only to new sessions, or can he edit an in-progress session? If he can edit mid-session, when does the change take effect?
- Are there bounds on the durations (e.g., min 1 min, max 120 min)? Or can he set a 1-second session as a joke? The directive doesn't say.
