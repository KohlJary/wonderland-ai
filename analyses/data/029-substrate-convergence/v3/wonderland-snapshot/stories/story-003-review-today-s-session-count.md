## Story 003: Review today's session count

**Persona:** Priya, 41, a manager who uses pomodoro to model focus culture for her team. At the end of each day, she glances at the app to see how many focus blocks she actually completed, as a reality check against her perception.

**Situation:**

It's 5 PM. Priya wants a quick, non-judgmental view of her day: how many sessions did she actually complete? This is a 5-second glance, not a deep dive.

**Need:**

As Priya, I want to see today's session count (and break count, if useful) at a glance on the main screen, so that I can track whether my self-perception matches reality.

**Acceptance:**
- The main screen shows today's date and completed session count (e.g., '6 sessions')
- This number is visible without scrolling or navigating
- The number updates in real-time as sessions complete
- Priya can tap to see the times of each session if she wants detail, but doesn't have to

**Tier:** core

**Confusion-flags:**
- Should today's count reset at midnight, or at a user-configurable time?
- Does 'today' mean local midnight or UTC? For a single-user app, this should be obvious, but it often isn't.
- Should the count include breaks, or just sessions?
