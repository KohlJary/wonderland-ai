## Ticket 025: BLOCKING: Dormouse specifies session-audit and session-telemetry observability hooks

**Sources:** adr-002-add-minimal-session-audit-layer-for-incident-response-visibility, observation-dormouse-session-audit-hooks-are-load-bearing
**Owner:** dormouse
**Tier:** v1
**Estimate:** immediate specification required
**Status:** open

**Dependencies:**
- Blocks: implement-minimal-session-audit-layer-for-incident-response-visibility
- Blocked by: —
- Soft: specify-session-audit-log-format-for-breach-investigation

**Description:**

The Cat's session-audit layer (ADR-002) is the foundation for both the Queen's breach investigation and the Tweedles' unlock verification. But the Dormouse (who owns observability) has not yet specified what must be *visible* in production. Before the Tweedles implement the session layer, specify: (1) Session-creation telemetry: success rate, failure reasons, token collision detection? (2) Session-access audit shape: every request logged, or sampled? (3) Session-revocation verification: how will the Dormouse confirm that a revoked session is actually rejected on the next request? (4) Performance hooks: is the session layer adding latency to every /login request? By how much? Without this spec, the session layer ships unobservable and the Dormouse cannot 'wake when production tells the truth' per his §I responsibility.

**Acceptance:**
- Dormouse has specified the telemetry hooks (metrics, logs, traces) required for session-layer observability
- Specification includes sampling strategy (full logging vs sampled) and performance SLA (max latency added to /login)
- Cat confirms the session-layer architecture can accommodate these hooks without violating the SLA

**Risk:**

If the Dormouse over-specifies (e.g., full request logging of every session access), the session layer becomes a bottleneck and the rate-limit doesn't actually halt the attack (it just moves the bottleneck). If the Dormouse under-specifies, the session layer ships unobservable and future production incidents go unseen.
