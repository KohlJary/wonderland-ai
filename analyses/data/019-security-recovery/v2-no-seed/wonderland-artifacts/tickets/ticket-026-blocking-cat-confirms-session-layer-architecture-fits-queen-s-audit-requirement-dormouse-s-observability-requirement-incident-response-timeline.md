## Ticket 026: BLOCKING: Cat confirms session-layer architecture fits Queen's audit requirement + Dormouse's observability requirement + incident-response timeline

**Sources:** adr-002-add-minimal-session-audit-layer-for-incident-response-visibility, concern-dormouse-session-audit-hooks-are-load-bearing-for-unlock-and-investigation
**Owner:** cheshire_cat
**Tier:** v1
**Estimate:** immediate confirmation required
**Status:** open

**Dependencies:**
- Blocks: implement-minimal-session-audit-layer-for-incident-response-visibility
- Blocked by: specify-session-audit-log-format-for-breach-investigation, specify-session-telemetry-observability-hooks-required-for-production-incident-response
- Soft: —

**Description:**

The Cat has proposed the session-audit layer (ADR-002) as the load-bearing architectural surface for incident response. But the Cat has not yet confirmed that the proposed architecture can simultaneously satisfy: (1) Queen's requirement for 'session audit trails complete enough to answer what did this session access?' (2) Dormouse's observability requirement (TBD in the blocking ticket above), (3) Incident-response timeline constraint (implementation in <90 minutes). If the Queen's audit requirement (full request logging) and the Dormouse's observability requirement (performance SLA on /login latency) are in tension, the Cat must surface that tension and propose a resolution before the Tweedles implement. If the session layer cannot be implemented in <90 minutes with both constraints met, the Cat must propose an alternative architecture or an acceptable degradation.

**Acceptance:**
- Cat has confirmed (or refuted) that the proposed session-layer architecture satisfies both Queen's audit and Dormouse's observability constraints
- If constraints are in tension, Cat has proposed a resolution (e.g., sample audit logging, async telemetry export) and estimated the cost
- Tweedles have confirmed they can implement the confirmed architecture in <90 minutes

**Risk:**

If the Cat's proposed architecture cannot satisfy both constraints within the timeline, the incident-response scope must shrink (defer full audit logging to post-incident, or defer full observability to post-incident). The team needs to understand that tradeoff before the Tweedles start building.
