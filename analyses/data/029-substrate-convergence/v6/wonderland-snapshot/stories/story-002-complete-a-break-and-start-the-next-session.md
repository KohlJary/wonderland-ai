## Story 002: Complete a break and start the next session

**Persona:** Yuki, 34, a designer and manager who timeboxes her day into focus blocks and breaks. She is rigorous about breaks — sits away from the screen, makes tea, resets — but only if the break timer actually makes her stop.

**Situation:**

Yuki's 25-minute session has ended. The app notified her. She has 5 minutes to step away before the next session begins.

**Need:**

As Yuki, I want the break timer to feel like a real boundary — not a suggestion — so that I actually take the break instead of diving into the next task and losing the benefit of the pomodoro structure.

**Acceptance:**
- The break timer starts automatically after the session ends (I don't have to take an extra action)
- I can see how much break time remains, and it is easy to dismiss the break and start the next session early if I need to, but that action is deliberate (not accidental)
- When the break ends, I get a notification, and I can immediately start the next session, or I can step away and let the app wait

**Tier:** core

**Confusion-flags:**
- Should the break timer be as prominent as the session timer, or quieter? The right answer probably differs by user, which suggests settings — but this is v1.
- What if the user ignores the break timer for 10 minutes? Does the app assume they are done for the day, or does it wait indefinitely? This is a state-machine question we need to answer.
