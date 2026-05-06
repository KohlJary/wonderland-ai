# ADR-001: Translation processing location and data residency model under GDPR

## Context

Four user stories now form a coherent picture: monolingual users need real-time translation; polyglot moderators need to manage cross-language threads without cognitive overload; language-pair expansion (Japanese entering English-German) must not require English as a bridge; and new users must authenticate without friction. Collectively, these stories imply two architectural seams: (1) message flow and translation latency, and (2) data handling and regulatory compliance. The Queen has surfaced that GDPR applies and that translation introduces a data-processor decision. The stories show us why: messages are exchanged in plaintext, translation happens on demand, and non-EU language pairs (Japanese) are in scope. The architecture must answer: where does translation happen, who sees plaintext, and what data residency guarantees do we give users?

## Decision

Adopt server-side translation with EU-hosted, GDPR-compliant third-party service (DeepL or equivalent under DPA). Store message content (plaintext and translated) in EU-only database with 90-day retention policy (configurable per user consent). Authentication via HTTPS-enforced username/password with bcrypt hashing. Translation service selection deferred to Tweedles' procurement phase (which service, which DPA terms, which latency SLAs) but architecture assumes third-party. In-house translation deferred to v2 (requires model sourcing, training-data provenance, operational overhead that exceeds three-week timeline). Hybrid (encrypt-then-translate on device) deferred as well—complexity cost exceeds MVP scope and latency cost is unacceptable for synchronous cross-language threads.

## Tradeoffs

- Third-party translation service means plaintext transits to external processor. Mitigated by: DPA contract, EU data residency, message retention policy. Cost: procurement overhead, ongoing service fees, vendor dependency.
- Server-side translation (vs. device-side) means server sees plaintext. Accepted because: (a) server is under our control, (b) user consent is explicit (part of auth flow), (c) EU data residency is enforceable, (d) device-side translation for Japanese-to-German (non-English pairs) would require multi-language models on device, which is not feasible in MVP.
- 90-day retention closes the door on long-term message archives and full conversation history export (common in chat applications). Accepted because: GDPR minimization principle suggests shorter is better; users can screenshot; v2 can offer paid long-term storage under explicit user retention requests.
- Basic auth (username/password) instead of federated/SSO. Accepted for MVP scope, but means we own password security (TLS, hashing, breach notification). Defers to v2: OAuth2/OIDC integrations.
- Two-language pairs at launch (English ↔ German, English ↔ Japanese) instead of arbitrary n-language graph. Accepted. Japanese ↔ German bridging via English is not in scope (polyglot moderator story implies moderators handle translation, not the system). Architecture does not preclude n-language expansion in v2.
- Message immutability (no edit, no delete in v1). Accepted because: simplifies retention/audit compliance, reduces re-translation logic, aligns with regulatory audit trails (immutable records are easier to defend). Cost: users cannot fix typos. Deferred to v2.
- Three-week timeline is aggressive for GDPR-compliant infrastructure. Achievable if: Queen's rulings on consent/retention/DPA are crisp (not iterative); Tweedles' procurement of translation service completes within week 1; contract negotiation with service (DPA terms) completes within week 1.5. If any of these slip, compliance does not ship with v1.

## Status

Proposed
