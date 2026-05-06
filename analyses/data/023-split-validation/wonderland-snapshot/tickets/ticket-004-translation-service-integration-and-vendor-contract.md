## Ticket 004: Translation service integration and vendor contract

**Sources:** adr: user-language-capability-model-message-translation-surface
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1-1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: message-send-and-receive-api-endpoints
- Blocked by: message-model-with-translation-surface
- Soft: queen-ruling-on-vendor-dpa-and-article-28-compliance

**Description:**

Integrate with translation vendor (Google Translate API, DeepL, or per Cat's proposal). Implement translation call in message GET handler. Include error handling (vendor unavailable → return original text + warning to frontend). Document data flow for Queen's DPA review. No context sent (just current message, not conversation history) per ADR. API key management and rate-limiting per vendor terms.

**Acceptance:**
- Translation API client implemented (handles auth, rate limits, retries)
- Message GET calls translation service and returns translated text
- Vendor error (timeout, invalid key, rate limit) returns original text + frontend-visible warning
- Data flow document ready for Queen: what PII leaves the system, to where, under what conditions
- No conversation history sent; only current message

**Risk:**

Vendor choice not yet finalized. If Cat or Alice object to the choice (cost, privacy, quality), may require reconsideration. Also: Queen's DPA review may require retry logic, encryption in transit, or other controls that extend estimate to 2 days.
