## Ticket 005: Frontend consent flow and language-preference form

**Sources:** user-joins-from-eu-and-sees-privacy-consent-flow, user-logs-in-from-a-second-device
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: session-initialization-language-preference-and-consent-basis-capture
- Soft: —

**Description:**

UI flows for EU users: on first session, show consent dialog explaining translation processing, with accept/decline/learn-more options. Separately: language-preference selection (source and target language dropdowns or auto-detection with override). These are gated: consent screen appears first, language preference appears after consent is given (or never, for non-EU users).

**Acceptance:**
- EU users see consent dialog on first session initialization
- Non-EU users skip consent dialog entirely
- Consent state persists across page reloads within the same session
- Multi-device sessions show consent dialog independently (no shared consent state)
- Language-preference form appears after consent is accepted
- Language choices persist in session state

**Risk:**

If legal/compliance wants copy approval on the consent dialog, add 1–2 days for review cycle. Estimate assumes copy is approved or delegated to the Queen's ruling. Also: if the Queen's consent documentation is not finalized, this blocks on ticket 2.
