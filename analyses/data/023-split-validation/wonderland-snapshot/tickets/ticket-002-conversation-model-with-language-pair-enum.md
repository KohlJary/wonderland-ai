## Ticket 002: Conversation model with language_pair enum

**Sources:** adr: user-language-capability-model-message-translation-surface, story: monolingual-book-club-member-joins-cross-language-conversation
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.5-1 day, 85% confident
**Status:** open

**Dependencies:**
- Blocks: message-model-with-translation-surface, conversation-listing-and-creation-api
- Blocked by: user-model-with-language-capability-schema
- Soft: —

**Description:**

Define Conversation(id, user_a_id, user_b_id, language_pair enum, created_at). Language_pair is immutable (e.g., 'en_de', 'en_ja', 'de_ja'). Foreign keys enforce two-user constraint. No deletion/edit in v1.

**Acceptance:**
- Conversation table exists with correct schema
- Enum values cover MVP language pairs (en_de, en_ja, de_ja, or per final list)
- Foreign key constraints prevent orphaned conversations

**Risk:**

Language_pair enum scope needs final confirmation from Alice/Cat (which pairs are in MVP). If list grows, expand estimate minimally.
