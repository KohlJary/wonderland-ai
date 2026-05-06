## Ticket 005: Japanese speaker can join German-English book club without English as fallback

**Sources:** story/japanese-speaker-enters-german-english-book-club-without-english-as-fallback
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 1.5–2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket/translation-backend, ticket/auth-flow
- Soft: —

**Description:**

Implement the three-language support in message composition and display for the japanese-speaker story. Scope: user can compose message in Japanese, it displays with German and English translations in the thread, other users see translations in their preferred language. Use translation backend. Out of scope: language preference settings, auto-detection of user language, per-user translation quality tuning. Keep it simple: user types in Japanese, system handles the rest.

**Acceptance:**
- Japanese message composes and sends successfully
- German and English translations appear in thread
- Other users see translations in the thread
- User who sent Japanese message sees their own message in Japanese

**Risk:**

Low to moderate. Potential for translation service rate limits with three concurrent translations per message. Test with realistic thread velocity.
