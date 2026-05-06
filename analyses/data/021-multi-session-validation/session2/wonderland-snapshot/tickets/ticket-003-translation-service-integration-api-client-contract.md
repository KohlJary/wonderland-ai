## Ticket 003: Translation service integration (API client + contract)

**Sources:** adr:translation-chat-data-model-persistence-translation-service-risk-and-user-identity
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1–2 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: ticket:message-send-receive-pipeline
- Blocked by: —
- Soft: ticket:schema-and-persistence-layer

**Description:**

Implement client for an external translation service (e.g., Google Translate API, DeepL). Create a wrapper function that accepts text and target language and returns translated text. Implement retry logic and timeout handling (max 3s per request). Log service failures; do not hard-fail chat on translation service outage (fail gracefully: return original text with a flag). Negotiate with Tweedledee on the contract: what does the client interface look like? Are translations cached? Error handling strategy? Do not implement caching in v1; defer to fast-follow.

**Acceptance:**
- Translation API client accepts text and target language
- Client returns translated text or original text + error flag on service failure
- Timeout is enforced (≤3s per request)
- Retry logic is implemented (max 3 attempts)
- Chat flow does not hard-fail if translation service is down

**Risk:**

ADR names 'translation service risk' as open. High-latency translation service will slow down message send/receive. Coordinate with Tweedledee on acceptable latency budget and whether translations should be asynchronous (sent after message is delivered). This is a Tweedle contract negotiation.
