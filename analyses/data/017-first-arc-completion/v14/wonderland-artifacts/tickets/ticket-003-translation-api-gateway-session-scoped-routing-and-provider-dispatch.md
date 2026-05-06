## Ticket 003: Translation API gateway: session-scoped routing and provider dispatch

**Sources:** monolingual-user-sends-message-across-language-boundary, user-joins-from-eu-and-sees-privacy-consent-flow
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1.5–2.5 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: message-enrichment-on-send, message-enrichment-on-receive
- Blocked by: message-contract-translation-metadata-and-original-text-carrier, session-initialization-language-preference-and-consent-basis-capture
- Soft: —

**Description:**

Build the gateway that sits between the message layer and the translation provider. It reads session state (language preference, consent flag, provider selection) and either routes to the translation provider or short-circuits (no translation if consent not given or languages match). Includes retry logic, error handling, and fallback to no-translation if provider is unavailable. This is the bridge between session state and message enrichment.

**Acceptance:**
- Session state is read and respected (no translation if consent missing)
- Provider dispatch is deterministic based on session language preferences
- Failures in translation provider do not block message delivery
- Translated and original text both flow through the gateway

**Risk:**

If the translation provider API contract changes mid-development, this ticket extends significantly. Estimate assumes provider API is stable. Also: if the Caterpillar flags state-management issues in review, rework could add 0.5 days.
