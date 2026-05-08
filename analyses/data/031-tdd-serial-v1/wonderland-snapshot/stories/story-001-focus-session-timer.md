## Story 001: Focus Session Timer

**Persona:** Marcus, 28, software engineer, uses Pomodoros to protect deep work from Slack interruptions. Works from home with a toddler and needs clear visual/audio signals when his focus time ends.

**Situation:**

Marcus sits down to code. He has 25 minutes before his next meeting. He needs the timer to be obvious and to announce itself loudly enough that he can hear it from the kitchen when he steps away for water.

**Need:**

As Marcus, I want to start a focus session timer that counts down visibly and alerts me audibly when time is up, so that I can step away at a clear boundary without watching the clock.

**Acceptance:**
- Timer starts on one tap/click and displays remaining time prominently
- Audio alert plays when focus session ends (configurable volume)
- Visual indicator (color change, animation) signals the end of session before sound plays
- Default is 25 minutes; timer is pausable but not restartable mid-session

**Tier:** core

**Confusion-flags:**
- Unclear: does pausing mean Marcus can resume from where he paused, or does any pause = abandoning the session? (affects reset behavior)
- Unclear: what happens if the browser tab loses focus mid-timer — does it keep counting? Does the alert still fire?
