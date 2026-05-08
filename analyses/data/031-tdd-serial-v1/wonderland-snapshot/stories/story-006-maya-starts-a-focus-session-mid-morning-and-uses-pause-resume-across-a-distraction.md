## Story 006: Maya starts a focus session mid-morning and uses pause-resume across a distraction

**Persona:** Maya, 31, polyglot content moderator. Works from a noisy coffee shop. Context-switches constantly between moderated threads in different languages.

**Situation:**

Maya has 25 minutes before her next meeting. She starts a focus session to triage the backlog of flagged posts. Three minutes in, a colleague drops by with an urgent question. She doesn't want to lose her session — she wants to pause it, answer the question (2–3 minutes), and resume.

**Need:**

As Maya, I want to pause my timer without losing elapsed progress, answer real-world interruptions, and resume from exactly where I paused, so that I can reclaim focus time when the interruption ends.

**Acceptance:**
- Session starts and timer counts down visibly
- Pause button is available during an active session
- Clicking pause freezes the countdown at the exact moment (no rounding)
- Elapsed time shows the work done before pause
- Resume button is available while paused
- Clicking resume continues counting down from the paused time (not reset)
- Multiple pause/resume cycles on the same session accumulate elapsed correctly
- No audio/visual alerts fire while paused

**Tier:** core

**Confusion-flags:**
- I'm not sure how 'focus' feels in a high-interruption environment — the timer is meant to protect attention, but interruptions are real. Is the pause-resume cycle the right affordance, or does it just delay frustration?
- What happens to a paused session if the user walks away for 30 minutes? Does it auto-resume, timeout, or stay paused forever? The contract note says it doesn't auto-resume, but the UX of that feels fragile.
