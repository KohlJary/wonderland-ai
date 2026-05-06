## Ticket 002: Implement streaming translate-on-send service

**Sources:** adr#1: translation-as-unit-level-transformation-not-stream-level-transport, story: monolingual-book-club-member-joins-a-cross-language-discussion
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1.5-2.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: dual-display-message-ui
- Blocked by: design-and-implement-message-schema-with-original-translation-unit-storage
- Soft: —

**Description:**

Build the translation service that handles the translate-on-send flow. Accepts (original_text, original_language, target_language), calls the translation model (assume Claude Haiku 4.5 for budget reasons; if team chooses otherwise, confirm model selection before starting), streams results back to the caller, and returns (translated_text, confidence_estimate). Include error handling for translation failures (model timeout, language-pair unsupported). Do not integrate with the message storage layer yet; assume the caller (Tweedledee) will handle saving the result. Service must be callable from both backend API and (for testing) from the browser console.

**Acceptance:**
- Service accepts (original_text, original_language, target_language) and returns (translated_text, confidence_estimate) within 2-3 seconds for typical message length (< 500 chars)
- Service handles language-pair not supported gracefully (returns error, not crash)
- Integration test: end-to-end translate call with mock message storage
- Contract note documents the service API (input/output shape, error codes, latency guarantees)

**Risk:**

Claude Haiku 4.5 latency under load is unknown; if 2-3 second SLA is not achievable, fast-follow to cached translations or model-specific optimization. Language detection (user says 'translate to X' but original language is unclear) is out of scope for v1; assume original language is explicit in the UI.
