## Ticket 009: Extend ADR-002: blocked-sender error visibility contract

**Sources:** story slug=block-a-user-who-is-bothering-me, adr slug=user-blocking-additive-model-with-silent-blocking-semantics
**Owner:** cheshire_cat
**Tier:** v1
**Estimate:** 0.5 days, 85% confident
**Status:** open

**Dependencies:**
- Blocks: ticket slug=blocking-endpoints-post-get-delete-blocks-with-message-send-gate
- Blocked by: —
- Soft: —

**Description:**

ADR-002 names the 403 return code for blocked sends but leaves the error payload unspecified. Decide: does the error message tell the sender they are blocked ('You are blocked by this user'), or is it generic ('Message failed to send')? This choice affects frontend error handling, user understanding, and GDPR notice obligations. Document the tradeoff explicitly in ADR-002's tradeoffs section with the privacy/clarity tension and any compliance implications. The Tweedles need this contract before they build the message-send gate.

**Acceptance:**
- ADR-002 tradeoffs section explicitly names the blocked-sender visibility choice
- Error payload shape is specified (either revealing or generic)
- GDPR implications of the choice are surfaced and documented
- Tweedles acknowledge the contract and confirm gate implementation plan

**Risk:**

If the compliance implications are deeper than expected (e.g., 'blocked by' is personal data that triggers notice requirements), the answer may cascade to Queen review. Cat and Queen should coordinate before the ADR ships.
