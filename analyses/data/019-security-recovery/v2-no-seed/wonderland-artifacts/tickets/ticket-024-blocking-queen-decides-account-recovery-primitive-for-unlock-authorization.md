## Ticket 024: BLOCKING: Queen decides account-recovery primitive for unlock authorization

**Sources:** adr-001-decouple-unlock-authorization-from-initial-authentication, ruling-009-unlock-must-not-be-possible-for-attackers-with-breached-password
**Owner:** queen_of_hearts
**Tier:** v1
**Estimate:** immediate decision required
**Status:** open

**Dependencies:**
- Blocks: implement-account-recovery-primitive-validate-email-ownership-for-unlock-authorization, update-login-lockout-ux-for-already-locked-out-users, add-unlock-account-cta-to-login-page-for-locked-out-users-who-know-their-credentials
- Blocked by: —
- Soft: —

**Description:**

The unlock path (per ADR-001) requires decoupling from password-based authentication. Which recovery primitive should the Tweedles implement? Email token (simplest, 10-30min UX friction)? SMS OTP (faster, ~5min)? Security questions (no external dependency, depends on pre-enrollment)? FIDO2 (most secure, assumes user hardware)? Specify the primitive, the threat model it satisfies, and the UX requirement (sync vs async, retry limits, fallback if primary fails). This decision gates ticket #19 (implement account-recovery primitive) and all downstream unlock UX work.

**Acceptance:**
- Queen has selected one recovery primitive and documented the threat model it satisfies
- Primitive choice includes operational requirements (SLA, retry limits, fallback)
- Tweedles confirm the primitive can be implemented and deployed in <90 minutes

**Risk:**

If the Queen defers the decision, the unlock path stalls. If the Queen selects a primitive that requires external integration (SMS provider, FIDO2 enrollment service) that does not exist yet, the scope expands and the ETA extends beyond the incident-response window.
