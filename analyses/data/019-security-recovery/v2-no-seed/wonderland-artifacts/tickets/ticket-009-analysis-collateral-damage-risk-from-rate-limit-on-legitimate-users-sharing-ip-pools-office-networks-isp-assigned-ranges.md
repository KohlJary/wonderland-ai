## Ticket 009: Analysis: Collateral-damage risk from rate-limit on legitimate users sharing IP pools (office networks, ISP-assigned ranges)

**Sources:** test_scenario slug=legitimate-user-from-office-network-shared-ip-is-collateral-locked-during-credential-stuffing-attack-originating-from-adjacent-network-segment
**Owner:** Dormouse
**Tier:** fast-follow
**Estimate:** 0.5-1 day, 85% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket slug=implement-rate-limiting-on-login-endpoint-per-queen-ruling
- Soft: ticket slug=implement-account-unlock-workflow-for-rate-limited-users-email-link-or-sms

**Description:**

The rate-limit in the immediate mitigation is source-IP-based. This creates a known risk: legitimate users behind a shared IP (office network, ISP-assigned pool) may be rate-limited as collateral when an attacker uses the same source IP pool. The Hatter's scenario (#4) surfaces this directly. We need to understand the scope: how many of our users access from IP pools that are shared or dynamic? Can we mitigate the collateral damage (e.g., whitelisting known office networks, requiring email verification for unlock instead of waiting out the rate-limit timeout)? Document the risk, the mitigation options, and the residual exposure. This informs whether the rate-limit + lockout policy is acceptable or whether we need a secondary auth factor (email, SMS) for recovery.

**Acceptance:**
- Documented estimate of legitimate user collateral damage (% of users behind shared IP pools, estimated lockout frequency)
- Documented mitigation options (IP whitelist, email unlock flow, SMS unlock flow, timeout reduction)
- Recommendation for whether the rate-limit + lockout policy is acceptable or requires secondary auth factor
- If secondary auth is required, ticket created for implementation

**Risk:**

This is analysis, not implementation. If the collateral damage is high and secondary auth is required, we may need to reopen the unlock-workflow tickets to add email/SMS primitives. Plan for escalation to the Queen if the analysis recommends changes to her rate-limit ruling.
