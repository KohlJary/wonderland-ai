## Ticket 001: Message contract: translation metadata and original-text carrier

**Sources:** monolingual-user-sends-message-across-language-boundary, user-receives-translated-message-and-wants-to-see-the-original
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: session-state-carrier-for-translation-context, frontend-message-display-with-original-text-toggle
- Blocked by: —
- Soft: —

**Description:**

Define the message schema to carry both translated and original text, with metadata for translation source language, target language, and translation provider. Include versioning so future translation providers can extend the schema without collision. This is the contract the frontend binds to and the session layer persists.

**Acceptance:**
- Message schema includes original_text, translated_text, source_language, target_language, translation_provider fields
- Schema versioning strategy documented
- Backwards-compatible with existing message schema in the hub model

**Risk:**

If translation provider selection logic is not settled, this ticket may need to loop back to the Cat for an architectural clarification. Estimate assumes provider selection is already decided in the ADR.
