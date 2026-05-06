## Ticket 006: Message enrichment on send and receive

**Sources:** monolingual-user-sends-message-across-language-boundary, non-english-speaker-initiates-conversation-with-english-only-user
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: translation-api-gateway-session-scoped-routing-and-provider-dispatch, message-contract-translation-metadata-and-original-text-carrier
- Soft: —

**Description:**

Wire the translation gateway into the message send and receive flows. On send: translate the outgoing message if session consent allows, store both original and translated in the message contract. On receive: translate the incoming message if the recipient's session preference differs from the sender's language, store both versions. This is the orchestration layer that makes end-to-end translation flow happen.

**Acceptance:**
- Outgoing message is translated before storage if consent is given and languages differ
- Incoming message is translated on receipt if recipient language differs
- Both original and translated versions are stored in the message contract
- If translation fails, message is stored with original text only (no translation)

**Risk:**

Low risk on this ticket because the heavy lifting is in tickets 2 and 3. Main risk is async translation (if provider is slow) — estimate assumes synchronous translation with timeout fallback.
