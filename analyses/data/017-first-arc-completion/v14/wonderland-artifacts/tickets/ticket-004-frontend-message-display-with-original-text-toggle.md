## Ticket 004: Frontend message display with original-text toggle

**Sources:** monolingual-user-sends-message-across-language-boundary, user-receives-translated-message-and-wants-to-see-the-original
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: message-contract-translation-metadata-and-original-text-carrier
- Soft: translation-api-gateway-session-scoped-routing-and-provider-dispatch

**Description:**

UI component that displays a message and, if the message has both translated and original text, shows a toggle to switch between them. Include language labels so the user knows which is which. This is the surface that makes the translation visible to the user without requiring a second request.

**Acceptance:**
- Message with translated text renders both versions
- Toggle switches cleanly between original and translated with no reflow
- Language labels are always visible (e.g., 'Original: [ES]' vs 'Translated: [EN]')
- Messages without translation (language match or consent missing) show single text, no toggle

**Risk:**

If the design team wants animated transitions between original/translated, this could extend by 0.5 days. Estimate assumes static toggle.
