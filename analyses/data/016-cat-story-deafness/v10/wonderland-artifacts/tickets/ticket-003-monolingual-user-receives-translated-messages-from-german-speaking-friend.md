## Ticket 003: Monolingual user receives translated messages from German-speaking friend

**Sources:** story/monolingual-book-club-member-exchanges-messages-with-german-speaking-friend
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 1.5–2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket/translation-backend, ticket/auth-flow
- Soft: —

**Description:**

Implement the message display layer for the monolingual-exchange story. Scope: when a message arrives in German, display it with inline translation below the original, attribution to translator, and a 'show original' toggle. Use the translation backend endpoint. Out of scope: translation quality feedback, translation history, per-language rendering preferences. Keep the UX simple — the message, the translation, the toggle.

**Acceptance:**
- German message displays with inline English translation
- Original and translation both visible by default
- 'Show original' toggle works
- Attribution ('Translated by [provider]') displays
- No double-translation when user toggles between original/translation

**Risk:**

Very low. Straightforward display logic once translation backend is live.
