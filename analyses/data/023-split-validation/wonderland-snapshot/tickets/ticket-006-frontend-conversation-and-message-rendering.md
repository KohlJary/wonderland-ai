## Ticket 006: Frontend conversation and message rendering

**Sources:** story: monolingual-book-club-member-joins-cross-language-conversation, story: polyglot-moderator-manages-multi-language-thread
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 2-2.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: message-send-and-receive-api-endpoints
- Soft: basic-auth-ui

**Description:**

Build conversation list view (show active conversation with language pair). Build message thread view: messages rendered with sender name, timestamp, original language label, and dual-text display (original + translation side-by-side). Build message input field (text + language selector, or infer from user profile). No edit/delete UI in v1. Typing indicators and delivery status are fast-follow.

**Acceptance:**
- Conversation list displays with language pair label (e.g., 'en ↔ de')
- Message thread renders with sender name, timestamp, original language, and both original + translated text
- Message input field present with language selector (or language is inferred from User profile if profile specifies language)
- Send button posts to API; optimistic UI update (message appears immediately) with rollback on error
- Transcription is readable; layout does not break with variable-length translations

**Risk:**

Translation length variance (e.g., German is longer than English) could break layout. Estimate assumes flexbox layout; if rigid layout chosen earlier, expand to 3 days. Also: if language selector is needed on the input field, coordinate with backend on language validation.
