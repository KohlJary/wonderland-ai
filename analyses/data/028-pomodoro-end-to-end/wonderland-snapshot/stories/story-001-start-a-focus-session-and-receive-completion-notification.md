## Story 001: Start a focus session and receive completion notification

**Persona:** Marcus, 34, software engineer working from home. Easily distracted by Slack and email; uses the Pomodoro technique to protect deep work blocks.

**Situation:**

Marcus sits down at his desk with a coding task that needs 90 uninterrupted minutes. He wants to commit to a 25-minute focus block, silence notifications, and get a clear signal when the time is done so he can step away without checking the clock.

**Need:**

As Marcus, I want to tap a button to start a 25-minute timer that I can see counting down, and receive a clear notification when it ends, so that I can commit to focus without managing the clock myself.

**Acceptance:**
- The app shows a prominent button labeled 'Start Session' on the home screen
- Tapping it immediately begins a 25-minute countdown visible on screen
- The countdown updates every second and is readable from 3 feet away
- When the timer reaches zero, the app plays an audible notification (chime, tone, or alarm) and shows a visual alert
- The notification persists for 5 seconds or until dismissed
- The session is recorded as complete in the user's history

**Tier:** core

**Confusion-flags:**
- What happens if the user closes the app mid-session? Does the timer keep running in the background? (I assume it should, but I'm not certain what the UX expectation is here)
- Should the countdown be pausable, or is it a hard commitment? The directive doesn't specify; Pomodoro technique traditionally doesn't allow pausing mid-session
