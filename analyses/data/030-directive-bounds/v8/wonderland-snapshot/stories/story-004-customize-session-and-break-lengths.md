## Story 004: Customize session and break lengths

**Persona:** Yuki, 19, student, uses different session lengths for different subjects (45 minutes for math, 20 minutes for reading comprehension). Standard 25/5 pomodoro doesn't match how her brain works, and she has tried apps that force her into the standard.

**Situation:**

Yuki is configuring the app for the first time. She wants to set a 45-minute work session and 10-minute break, because that is what actually works for her focus. She also wants the option to set different lengths for different 'projects' or 'subjects', so she can switch contexts without reconfiguring.

**Need:**

As Yuki, I want to customize the session length and break length, and ideally have different presets for different kinds of work, so that the timer matches my actual focus rhythm instead of fighting it.

**Acceptance:**
- Settings screen lets me set a default session length and break length (both in minutes).
- I can create named presets (e.g., 'math: 45/10', 'reading: 20/5') and switch between them with one tap before starting a session.
- The app remembers my most-recent preset and defaults to it next time (but does not force it).

**Tier:** core

**Confusion-flags:**
- The 'projects' idea — Yuki wants different presets per subject, but the directive says no auth and single-user local app. This is still possible (store presets locally), but I'm not 100% sure whether the team will want this in v1 or as a fast-follow. Flagging it as real demand but acknowledging scope risk.
- There is a UI question about how to switch presets smoothly. Could be a dropdown before session start, could be buttons, could be a history of recent presets. Not my call, but worth the team knowing it matters.
