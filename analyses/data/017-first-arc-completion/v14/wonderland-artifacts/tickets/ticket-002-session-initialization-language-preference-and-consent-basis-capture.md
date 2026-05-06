## Ticket 002: Session initialization: language preference and consent-basis capture

**Sources:** user-joins-from-eu-and-sees-privacy-consent-flow, user-logs-in-from-a-second-device
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1–2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: frontend-consent-flow-and-language-preference-form, translation-api-gateway-session-routing
- Blocked by: —
- Soft: —

**Description:**

Extend session creation to capture user language preference (from browser Accept-Language or explicit user selection) and, for EU-based users, explicit consent for translation processing. Store both in session state keyed by device/user pair. The consent flow is gated: EU users see consent before any translation happens; non-EU users proceed without consent screen. This ticket is the backend contract; UI binding happens in ticket 5.

**Acceptance:**
- Session state includes user language preference (source and target)
- Session state includes EU consent flag and timestamp
- Multi-device sessions are independent (second device has its own consent/preference state)
- EU detection logic is implemented and testable

**Risk:**

GDPR consent-basis logic is complex; if the Queen's ruling on consent documentation is not yet finalized, this may need to loop back to her. Estimate assumes ruling is settled.
