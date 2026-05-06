## Story 010: Blocking works across language pairs (fast-follow)

**Persona:** Luis, 26, a Spanish-speaking user in an English-heavy group. He has blocked someone (could be any language). He wants to be sure the block applies no matter which language pair he's using in the app.

**Situation:**

Luis is chatting in English with one group and switches to Spanish with another. He's blocked someone who spans both conversations (unlikely but possible). He needs to be sure the block is global, not language-specific.

**Need:**

As Luis, I want to know that if I block someone, they're blocked across all my conversations and language pairs, not just one language.

**Acceptance:**
- Luis's block list is user-scoped, not language-pair-scoped
- A blocked person cannot send messages to Luis in any language pair

**Tier:** fast-follow

**Confusion-flags:**
- This might be obvious in the data model (blocks are user-to-user, not conversation-to-user), but I'm flagging it because it's easy to implement wrong if the block check is scoped to the conversation context instead of the user identity. The team should nail this early.
