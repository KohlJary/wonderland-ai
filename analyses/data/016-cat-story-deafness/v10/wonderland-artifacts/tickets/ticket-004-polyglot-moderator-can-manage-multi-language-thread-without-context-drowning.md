## Ticket 004: Polyglot moderator can manage multi-language thread without context drowning

**Sources:** story/polyglot-moderator-manages-cross-language-thread-without-drowning
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 2–3 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket/translation-backend, ticket/auth-flow
- Soft: —

**Description:**

Implement the thread management layer for the polyglot-moderator story. Scope: display all messages in moderator's native language by default (translation applied to German and Japanese inputs), show language badges next to messages, allow moderator to toggle between 'translated view' (all in their language) and 'original view' (with inline translations). Out of scope: language detection, moderation tools, thread folding. The moderator needs to see what people are actually saying without the cognitive load of context-switching.

**Acceptance:**
- All non-native messages translate to moderator's language by default
- Language badge displays on each message
- 'Translated view' / 'Original view' toggle works
- Switching views does not reload the page
- Moderator can see at least 3-message context at a time without scrolling

**Risk:**

Moderate. Translation API rate limits may bite if thread is very active. Flag for testing with high-volume scenario.
