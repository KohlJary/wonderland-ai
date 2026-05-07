## Story 007: Marcus runs a single focused 25-minute session and sees it complete

**Persona:** Marcus, 34, software engineer, uses the Pomodoro technique to protect deep work from calendar interruptions. He's skeptical of tools but willing to try one if it gets out of his way.

**Situation:**

Marcus has a 90-minute block for a task that requires sustained focus. He opens the timer app, sets the default 25-minute session, and starts it. No configuration needed — he trusts the defaults.

**Need:**

As Marcus, I want to start a work session and have a timer count down to zero with no interaction from me, so that I can focus on my work without watching the clock.

**Acceptance:**
- The timer starts immediately when Marcus clicks 'Start Session' (no additional forms or dialogs).
- The UI displays the countdown: minutes and seconds, updating at least once per second.
- When the countdown reaches 00:00, the timer emits an audible signal or visual notification that the session is complete.
- The session transitions to 'complete' state and does not re-start on its own.

**Tier:** core

**Confusion-flags:**
- What does 'audible signal' mean in a web app context? Browser notification, audio file, system sound? The acceptance criterion is vague about the mechanism.
- Does Marcus see a 'break time' timer next, or does the session end and he manually start the break? The feature claim says 'work session' — break might be Feature-002.
- Is there a visual indicator that the session is running (color change, pulsing element)? The criterion says 'displays the countdown' but doesn't specify how it signals active vs. idle state.
