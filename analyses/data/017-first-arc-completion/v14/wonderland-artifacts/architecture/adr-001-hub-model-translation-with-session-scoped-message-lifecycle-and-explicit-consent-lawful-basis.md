# ADR-001: Hub-model translation with session-scoped message lifecycle and explicit-consent lawful basis

## Context

The team has deferred three load-bearing decisions (Cat's hub/peer choice, Queen's data-handling questions, and the three-week vs. GDPR-compliance binding constraint). Alice's six stories now provide the architectural shape that makes the deferred decisions concrete and answerable.

The stories reveal: (1) cross-language user pairs exchanging messages synchronously (monolingual→translated→received→original-visible pattern), (2) single-device assumption in MVP (no multi-device sync story), (3) conversation isolation (wrong-conversation mistake implies conversation scoping, not global inbox), (4) explicit privacy consent as part of user onboarding, (5) no edit/delete scope means message immutability once sent.

These constraints collectively imply a three-week MVP with compliance-honest boundaries, not a full GDPR-compliant production system. The constraint is binding as: shippable in three weeks, with honest labeling of what 'compliant' means and what is deferred.

## Decision

Store messages in a transactional session model: each conversation persists only for the session lifetime. On logout, conversation history is purged. Translation is hub-routed (English as pivot) through a stateless, read-only third-party service (no cached translations, no model training on user data). Lawful basis is explicit consent: users see a privacy notice on signup that names (a) messages are translated via third-party service, (b) messages are purged on logout, (c) no persistent data processing occurs post-session, (d) this is an MVP and not production-grade. Users must affirm before proceeding. Auth is session-scoped; multi-device is out of scope for v1.

This architecture fits three weeks. It is not GDPR-compliant in the full audit sense (no persistent audit trail, no user-access mechanism for historical data, no retention policy for data that persists post-logout). But it is honest about what it is, and it avoids the compliance debt of building persistent infrastructure that does not yet have compliance built in.

## Tradeoffs

- Session-scoped storage avoids persistent data-handling infrastructure and retention-policy questions, but means users cannot resume conversations across logout-login cycles. This is acceptable for MVP; it trades persistence for simplicity.
- Hub-routed translation is cheaper to add language pairs to later and simpler to test, but means all translations route through English as pivot. This can distort idiom and cultural context (German→English→Japanese loses German-specific tone). Trade-off is acceptable for two-language-pair launch.
- Explicit-consent lawful basis is the only GDPR basis that does not require processor agreements or data-handling audits at MVP stage. It is also the most transparent to users. It trades legal certainty for MVP simplicity. A production system would likely need a richer basis (service provision, legitimate interest with balancing); for MVP, consent is appropriate.
- Third-party translation service (rather than self-hosted model) is required to ship in three weeks and avoids infrastructure toil. It trades data sovereignty for time-to-market. The consent notice must name the service and the fact that messages cross your boundary.
- Multi-device is deferred. The single-device assumption simplifies auth and session management. When multi-device is needed, it will require a persistent session model and revise this entire architecture.

## Status

Proposed
