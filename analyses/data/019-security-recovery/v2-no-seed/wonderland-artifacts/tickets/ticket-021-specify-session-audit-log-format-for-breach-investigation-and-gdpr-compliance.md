## Ticket 021: Specify session-audit log format for breach investigation and GDPR compliance

**Sources:** concern from Dormouse on session-audit observability requirements
**Owner:** Queen of Hearts
**Tier:** v1
**Estimate:** 0.5 days, 90% confident
**Status:** open

**Dependencies:**
- Blocks: implement-minimal-session-audit-layer-for-incident-response-visibility
- Blocked by: —
- Soft: adr slug=add-minimal-session-audit-layer-for-incident-response-visibility

**Description:**

Define the exact shape of the session-audit logs the Queen requires to answer 'what data did session X access?' within 72 hours of breach notification deadline. Must include: log fields (session_id, user_id, endpoint, timestamp, response_code, data_scope accessed), retention window (how long must logs be queryable?), sampling strategy (log all requests or sample at scale?), and any regulatory requirements (GDPR, SOC2, etc.). This spec gates the Tweedles' implementation of audit hooks in the session layer.

**Acceptance:**
- Queen has published the exact log schema she requires for breach investigation
- Retention window is specified (e.g., '72 hours queryable, 30 days archived')
- Sampling strategy is decided (log every request or sample?)
- Any compliance gates are named (GDPR Art. 32 / SOC2 C1 / etc.)

**Risk:**

If the Queen defers this spec, the Tweedles will guess at log format, implement something, and then the Queen will reject it as insufficient for investigation. Specify now; re-visit if investigation reveals gaps.
