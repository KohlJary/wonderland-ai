## Story 002: Take and track a break

**Persona:** Dev, 28, an IC engineer who uses the timer to batch interruptions. After each focus session, he checks Slack during the break. He wants breaks to feel intentional, not like wasted time.

**Situation:**

Dev's 25-minute session just ended. He's in a flow state. He wants the break timer to be equally visible as the session timer, so he doesn't accidentally extend it.

**Need:**

As Dev, I want the app to automatically prompt a 5-minute break after each session and show a countdown, so that I know when to return to work and don't drift into longer breaks.

**Acceptance:**
- When a session ends, the break timer starts immediately (or with a one-tap confirmation)
- The break countdown is as visible as the session countdown was
- When the break ends, a notification similar to the session-end notification fires
- Dev can see in history that both the session and the break completed

**Tier:** core

**Confusion-flags:**
- Should the break start automatically or wait for a tap? The difference is big for flow state.
- Can Dev skip or shorten a break, or is the timer rigid?
- Does pressing 'skip break' immediately start a new session, or return to idle?
