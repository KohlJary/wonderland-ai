## Story 001: Start and complete a focus session

**Persona:** Marcus, 34, a software engineer working from home with two kids. He loses track of time easily and often forgets to take breaks.

**Situation:**

It's 9 AM and Marcus has a block of uninterrupted time before his first meeting. He opens the app, starts a session, and wants to be freed from watching the clock.

**Need:**

As Marcus, I want to start a 25-minute focus session with a single tap and receive a clear notification when it ends, so that I can stop thinking about time and trust the app to tell me when to stop.

**Acceptance:**
- Tapping 'Start Session' immediately begins a 25-minute countdown
- The app displays remaining time in a clear, large format
- When the timer reaches zero, a notification interrupts (sound, vibration, or modal — platform-appropriate)
- The session is automatically recorded in history as complete
- The notification is dismissible and leads to the break screen

**Tier:** core

**Confusion-flags:**
- I don't know if Marcus is in the browser or a mobile app — the directive says 'app' but doesn't specify platform. This changes notification behavior entirely.
- What happens if he closes the browser/app mid-session? Does the timer keep running? Does the session get recorded as abandoned? This feels like it matters for his trust in the tool.
