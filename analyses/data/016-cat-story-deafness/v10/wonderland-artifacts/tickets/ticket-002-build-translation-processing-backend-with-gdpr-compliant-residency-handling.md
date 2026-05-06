## Ticket 002: Build translation processing backend with GDPR-compliant residency handling

**Sources:** adr/translation-processing-location-and-data-residency-model-under-gdpr
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 2–3.5 days, 60% confident
**Status:** open

**Dependencies:**
- Blocks: ticket/monolingual-exchange-frontend, ticket/polyglot-moderator-frontend, ticket/japanese-speaker-frontend
- Blocked by: ticket/auth-flow
- Soft: —

**Description:**

Implement the translation service abstraction per the Cat's ADR (adr/translation-processing-location-and-data-residency-model-under-gdpr). Scope: API endpoint that accepts text + source/target language codes, routes to translation provider based on user residency (EU users -> EU provider, others -> default), returns translated text and metadata (confidence, provider ID). Out of scope: caching layer, batch processing, provider fallover. The abstraction should be testable without calling live providers.

**Acceptance:**
- Translation endpoint accepts text and language pair
- Residency check correctly routes EU users to EU provider
- Response includes translated text and confidence metadata
- Non-EU requests route to default provider
- Endpoint is testable with mocked provider responses

**Risk:**

Provider API documentation may be incomplete. Expand to 4 days if integration testing requires live provider account setup. Queen's ruling on data handling may expand scope — flagging for early coordination.
