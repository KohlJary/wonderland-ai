## Story 005: Technical peer revokes collaboration after discovering incompatible working style

**Persona:** Klaus, 41, a senior engineer collaborating with Yuki on a real-time code review spanning multiple languages. Klaus is careful and methodical; after 30 minutes of conversation, Klaus realizes Yuki's communication style is too rapid-fire for Klaus to keep up with the translation latency.

**Situation:**

Klaus and Yuki are 30 minutes into a code review using the translation chat. Klaus has sent 15 messages in German; Yuki has sent 25 in Japanese. Klaus is falling behind—by the time he reads Yuki's translation, Yuki has already sent three follow-ups. Klaus wants to end this conversation without being rude, and he wants to ensure that his messages so far are not visible to Yuki going forward (he said some things in draft that were clarified later, and he does not want those to mislead her).

**Need:**

As Klaus, I want to block Yuki retroactively so that she cannot see my messages from this conversation point forward, and I don't see hers, and this doesn't feel like a rejection — it feels like a technical boundary.

**Acceptance:**
- Klaus can block Yuki from the conversation view
- After blocking, Klaus's messages sent before the block are hidden from Yuki's view (unlike Maya's scenario, Klaus needs retroactive occlusion)
- Yuki's messages sent before the block are hidden from Klaus's view
- The conversation does not disappear — Klaus can see that a conversation with Yuki existed, but the message history is redacted
- Both Klaus and Yuki see that a block is in effect (they know why the conversation is not progressing, rather than wondering if the other person is ignoring them)

**Tier:** enrichment

**Confusion-flags:**
- This story contradicts Story 001: Maya's block hides David's messages but David can still see the conversation; Klaus's block hides the entire message history bidirectionally. These are different blocking models — one is visibility-asymmetric, one is visibility-symmetric. The architecture can't serve both with a single model without explicit visibility contracts.
- The phrase 'block retroactively so that she cannot see my messages from this conversation point forward' is ambiguous: does it mean 'from now on' (future) or 'retroactively to this point' (past)? Klaus wants retroactive occlusion, but that contradicts the idea that 'messages sent before the block are visible.' Accepting this confusion-flag; the team needs to resolve what 'retroactive block' means.
- Does 'both see that a block is in effect' mean the block appears in the UI? Or just that the conversation stops progressing? If Yuki sees a notification 'Klaus has blocked you,' that's a notification surface; the scope says 'out of scope: blocking notifications.' But the acceptance criterion seems to require Yuki knowing a block happened.
