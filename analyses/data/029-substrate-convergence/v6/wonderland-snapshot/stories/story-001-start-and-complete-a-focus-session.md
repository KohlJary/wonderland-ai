## Story 001: Start and complete a focus session

**Persona:** Marcus, 28, a software engineer with ADHD who uses pomodoros to structure his workday. He has tried five different timer apps and abandoned them because they felt either too gamified or too sparse.

**Situation:**

Marcus sits down at his desk with a task he wants to focus on for the next stretch. He opens the app to start a session.

**Need:**

As Marcus, I want to start a 25-minute focus session with a single tap and have the app disappear so it doesn't distract me, so that I can actually focus without the tool becoming another source of friction.

**Acceptance:**
- Tapping 'Start Session' immediately begins a 25-minute countdown (not a confirmation dialog, not a settings screen — a single action)
- The app can be closed or minimized; the session continues and I get a visible notification when time is up
- The notification is clear (sound + visual) but not aggressive or startling
- Tapping the notification shows me the break timer has started automatically

**Tier:** core

**Confusion-flags:**
- What happens if the user closes the app entirely? Does the session continue in background? Does the OS keep the timer alive or does it die? This feels like a decision we haven't made.
- Is there a pause button during the session, or is pomodoro meant to be all-or-nothing? Different users will have strong opinions here.
- Does the app show elapsed time while in background, or only the notification? The difference changes whether it feels like a real timer.
