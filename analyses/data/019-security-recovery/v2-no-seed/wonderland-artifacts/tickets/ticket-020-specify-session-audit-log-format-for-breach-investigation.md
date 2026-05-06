## Ticket 020: Specify session-audit log format for breach investigation

**Sources:** cat-adr-002-session-audit-layer, dormouse-concern-observability-gaps-in-session-audit
**Owner:** cheshire_cat
**Tier:** v1
**Estimate:** 0.5-1 hour, 90% confident
**Status:** open

**Dependencies:**
- Blocks: ticket-implement-minimal-session-audit-layer
- Blocked by: —
- Soft: —

**Description:**

Formalize the audit log format that the Tweedles will write and the Dormouse will parse. Decision: does log include request body (PII risk), user ID (needed for breach scope), data-access classification (public vs sensitive), response status (succeeded vs failed)? Document the format as a contract between implementation and investigation. This spec must be complete before the Tweedles finalize the audit logging implementation, so the Dormouse can write the parsing logic in parallel.

**Acceptance:**
- Log format document includes: field names, data types, PII handling policy, sampling strategy (log all or sample?)
- Format is explicit about what constitutes 'sensitive data access' vs 'public access'
- Dormouse has reviewed and confirmed the format is parseable for 'did session X access sensitive data?' queries
- Queen has confirmed the format is sufficient for GDPR Article 33 breach investigation

**Risk:**

Format underspecified means Tweedles and Dormouse will guess, producing incompatible implementations. Mitigate: Cat publishes this first; Tweedles implement against it.
