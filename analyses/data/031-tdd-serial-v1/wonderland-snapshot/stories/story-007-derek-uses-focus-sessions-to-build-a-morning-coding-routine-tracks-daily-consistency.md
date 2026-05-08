## Story 007: Derek uses focus sessions to build a morning coding routine; tracks daily consistency

**Persona:** Derek, 27, backend engineer. Works from home. Recently committed to a 'focus block every morning' routine — three 25-minute sessions with breaks between. Uses the app to stay accountable.

**Situation:**

Derek's third focus session of the morning completes. He wants to see how many minutes he's actually accumulated today (did he really do three full blocks, or did he cut one short?). He also wants to know his 'streak' — how many consecutive days he's hit his goal (three completed sessions per day).

**Need:**

As Derek, I want to see my daily accumulated focus time and my streak of days where I hit my goal, so that I can stay accountable to my routine and feel progress.

**Acceptance:**
- Session completion is logged with completion_type and elapsed time
- Daily review shows total minutes across all sessions (completed + skipped + paused)
- Daily review shows number of completed sessions (skip and pause don't count as completion)
- Streak counter shows consecutive days where completed sessions >= threshold (e.g., 3 sessions × 25 min = 75 min/day)
- Streak resets if a day's target is missed
- Query is fast enough to load without perceptible lag (< 500ms)

**Tier:** core

**Confusion-flags:**
- Does 'completed' mean 'timer ran to 0' or 'timer ran to 0 AND audio played'? If audio fails, should the session still count as completed? Hatter's fragility test addresses audio failure, but the definition of 'completion' for streak purposes is unclear.
- Threshold for streak — is it 'at least 3 sessions per day' or 'at least 75 minutes'? They're not the same if sessions vary in duration. Derek might do four 20-minute sessions one day, missing the 75-minute goal but hitting four sessions. Which one unlocks the streak?
- Should paused sessions count toward daily total or not? They're work Derek did, but he abandoned them. I lean toward 'no,' but it feels like a decision that should be visible.
