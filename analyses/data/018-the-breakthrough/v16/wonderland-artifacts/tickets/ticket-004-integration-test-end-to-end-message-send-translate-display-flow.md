## Ticket 004: Integration test: end-to-end message send → translate → display flow

**Sources:** adr#1, all five stories
**Owner:** Tweedledee + Tweedledum (pair)
**Tier:** v1
**Estimate:** 0.5-1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: design-and-implement-message-schema-with-original-translation-unit-storage, translate-on-send-streaming-service, build-dual-display-message-ui-original-translation-side-by-side-with-hide-original-toggle
- Soft: —

**Description:**

Write an integration test that covers the happy path: user sends a message in German, the translate-on-send service is called, the translation arrives, the message is stored with both original and translation, the recipient's UI displays both. Test both directions (German→English and English→German). Test the failure case: translation service timeout or error, message is stored with original only, UI shows 'translation pending' or 'translation failed' gracefully.

**Acceptance:**
- Integration test runs green against v1 schema and service
- Happy path (translate succeeds): message stored and displayed with both original and translation
- Sad path (translate fails): message stored with original, UI shows error state and allows user to retry
- Both language directions tested
- Test is part of the CI/CD pipeline and runs on every commit

**Risk:**

If the translation service is non-deterministic (e.g., LLM output varies between calls), the test may be flaky. Consider using a mock translation service for integration tests, with a separate end-to-end test that uses the real service but is run less frequently.
