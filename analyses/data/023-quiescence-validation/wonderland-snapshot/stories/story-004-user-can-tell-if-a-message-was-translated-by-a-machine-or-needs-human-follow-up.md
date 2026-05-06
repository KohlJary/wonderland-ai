## Story 004: User can tell if a message was translated by a machine or needs human follow-up

**Persona:** Yuki, 34, Osaka. English-Japanese translator by training. She's chatting with an English speaker in a hobby community. She notices the translation is missing a cultural reference and wants to flag it without leaving the chat.

**Situation:**

Yuki receives a message from an English speaker that includes a colloquialism her translator probably fumbled. She wants to ask for clarification without having to abandon the chat.

**Need:**

As Yuki, I want to see some signal that a message was machine-translated (not human-verified), so that I know when to trust it implicitly and when to ask 'wait, what did you actually mean?'

**Acceptance:**
- Machine-translated messages have a visual marker (icon, color, badge — TBD) that human-approved or manually-written messages don't.
- The marker is subtle enough not to feel like every message is marked 'probably wrong,' but clear enough that I notice it when I need to.

**Tier:** fast-follow

**Confusion-flags:**
- This assumes there's a difference between machine-translated and human-verified in the system. I don't know if that's in scope — the directive says 'exchange messages with translation,' not 'exchange messages with human QA on translations.' I may be designing a feature that isn't wanted.
- Even if it is wanted, I don't know the workflow — does a human re-verify each translation? Or does 'human' mean 'the user can manually re-type it'? Or is this fast-follow precisely because we don't have a workflow for it yet?
