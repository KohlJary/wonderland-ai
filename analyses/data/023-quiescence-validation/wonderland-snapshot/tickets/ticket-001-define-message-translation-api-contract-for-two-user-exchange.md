## Ticket 001: Define Message + Translation API contract for two-user exchange

**Sources:** 001-two-monolingual-users-exchange-messages-in-their-native-language, message-translation-schema-asymmetric-visibility-model
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–2 days, 60% confident
**Status:** open

**Dependencies:**
- Blocks: backend-message-schema-and-storage, frontend-message-input-and-render
- Blocked by: —
- Soft: —

**Description:**

Produce the OpenAPI spec / JSON schema for POST /message and GET /conversation endpoints. The spec must support: (1) sender language + text, (2) target-user language preference, (3) translation artifact metadata (service used, confidence, human-verified flag). Design the response shape so original message + best-available translation(s) are returned in a single call. Leave translator service routing as a placeholder parameter in the spec — Queen's ruling and the business decision on translator source will inform the final implementation detail. The Caterpillar will review this contract before handoff to backend.

**Acceptance:**
- OpenAPI spec exists and is versioned in .wonderland/architecture/contracts/
- Spec covers Maya→Klaus and Klaus→Maya scenarios (monolingual exchange in native languages)
- Spec explicitly marks translator routing as a configurable parameter
- Caterpillar has reviewed and approved the contract

**Risk:**

Translation metadata shape may require iteration once we see what the chosen translator service actually returns. Plan for one refinement cycle.
