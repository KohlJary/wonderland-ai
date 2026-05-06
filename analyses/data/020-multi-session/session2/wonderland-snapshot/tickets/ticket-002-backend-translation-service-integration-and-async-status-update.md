## Ticket 002: Backend: Translation service integration and async status update

**Sources:** story-001, story-002, story-003, adr-message-visibility-and-audit-contract-dual-language-display-status-persistence-polling-based-sync
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 2–4 days, 60% confident
**Status:** open

**Dependencies:**
- Blocks: ticket-004
- Blocked by: ticket-001
- Soft: ticket-005

**Description:**

Integrate with external translation service (provider TBD by Cat or Queen; assume async API with polling or webhook). When a Message is created with translation_status = pending_translation, trigger an async job that calls the service with (original_text, source_language, target_language). On success, update translated_text and set translation_status = translated; on failure, set translation_status = translation_failed with error_code and error_message. Implement retry logic for transient failures (max 3 retries, exponential backoff). Log every translation attempt with timestamp and result.

**Acceptance:**
- Translation service is called asynchronously within 1 second of Message creation
- translated_text is populated on success
- translation_status transitions to translated on success, translation_failed on final failure
- Errors are logged with timestamp, error_code, and error_message
- Retry logic completes within 30 seconds or logs permanent failure
- Service outages do not crash the message creation API

**Risk:**

Translation service latency or availability unknown — if service is slow or flaky, retries could balloon. Expand to 4 days if service SLA is weak. If service requires synchronous calls, architecture changes; escalate to Cat.
