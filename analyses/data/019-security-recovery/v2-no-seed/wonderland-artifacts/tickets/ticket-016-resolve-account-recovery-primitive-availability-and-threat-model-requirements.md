## Ticket 016: Resolve account-recovery primitive availability and threat-model requirements

**Sources:** adr slug=decouple-unlock-authorization-from-initial-authentication, story slug=locked-out-user-regains-access-quickly-after-rate-limit-is-lifted
**Owner:** Cheshire Cat (decision owner), Queen of Hearts (threat-model authority), Tweedledee & Tweedledum (implementation feasibility)
**Tier:** v1
**Estimate:** 0.5 days, 85% confident (this is a decision, not code; the deciding is the work)
**Status:** open

**Dependencies:**
- Blocks: ticket slug=update-login-lockout-ux-for-already-locked-out-users, ticket slug=add-unlock-account-cta-to-login-page-for-locked-out-users-who-know-their-credentials
- Blocked by: —
- Soft: —

**Description:**

Unlock authorization cannot reuse the failed password (Cat's ADR is sound on this). But unlock needs a second factor that proves account ownership. The question is: what second factors already exist in the codebase as built primitives, and which does the threat model require?

The Cat must answer: 'Reading the codebase, we have [email-reset service / SMS-OTP service / security-question service / none of these]. The ADR assumes we can gate unlock on one of these. Is this assumption correct?'

The Tweedles must answer: 'If we need a recovery primitive that doesn't exist, what is the implementation scope? (Can we wire an existing third-party SMS provider in 2 hours, or do we need to build from scratch?)'

The Queen must answer: 'Threat-model-wise, which recovery primitives are acceptable for unlock authorization? (Email alone? SMS required? Security questions sufficient?)'

Once all three answers are on the table, the unlock UX tickets can proceed with a clear constraint boundary: 'implement unlock using [the recovery primitive the Queen requires, constrained to what exists or can be built in X hours].'

**Acceptance:**
- Cat confirms which account-recovery services exist in the codebase (built, not aspirational)
- Tweedles estimate the scope and risk of implementing any missing recovery primitive needed by the Queen
- Queen rules on which recovery primitive(s) satisfy the threat model for account unlock
- All three answers are visible on this ticket so the unlock UX tickets can reference the constraint when they ship

**Risk:**

If the recovery primitives don't exist and the Queen requires them, we're adding substantial scope during incident response. The Tweedles' estimate on 'build a recovery primitive in 2-4 hours' may be optimistic. Better to surface this now than discover it when the unlock UX tickets are already in flight.
