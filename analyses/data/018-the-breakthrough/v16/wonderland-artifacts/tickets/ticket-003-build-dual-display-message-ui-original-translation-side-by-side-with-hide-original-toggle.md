## Ticket 003: Build dual-display message UI: original + translation side-by-side with hide-original toggle

**Sources:** story: monolingual-book-club-member-joins-a-cross-language-discussion, story: english-only-speaker-joins-a-multilingual-group-chat, story: deaf-user-reads-live-captioned-cross-language-conversation
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 2-3 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: design-and-implement-message-schema-with-original-translation-unit-storage, translate-on-send-streaming-service
- Soft: —

**Description:**

Build the UI component that displays a message with both original and translation visible. Default: original on left, translation on right, both full-width in their lane. Include a toggle button to hide the original (e.g., 'Hide original' / 'Show original'). The toggle state should be remembered per-user session but not persisted to disk in v1 (Sophie's preference-persistence story is fast-follow). When a user sends a message in a non-English language, automatically translate to English (or the recipient's default language). Display the translation as it arrives from the streaming service (assume 2-3 second latency is visible and acceptable to the user). No accuracy signaling UI in v1 (Henrik's verification story is fast-follow).

**Acceptance:**
- Message displays with original + translation side-by-side, both readable without horizontal scroll
- Toggle button present and functional; hides/shows original text
- Streaming translation displays as it arrives (user sees partial translation as it compiles)
- Non-English message from user triggers automatic translation to English before display to recipient
- Accessibility: original and translation are both navigable via keyboard; screen reader announces both
- Contract note documents the message UI component API (props: message object with original/translation, callbacks for toggle state change)

**Risk:**

Streaming UI is complex; if the team has not shipped streaming components before, expand estimate to 3-4 days. Accessibility testing (especially for deaf/HoH users reading captions) should involve testing with actual captions (e.g., WebVTT or similar); if the UI is naive text-on-screen, it may not meet a11y standards. Flag for Caterpillar review.
