## Ticket 027: Extend account lockout threshold from 5 to 10 failed attempts (hotfix, ship immediately)

**Sources:** ruling-001
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 15 minutes, 95% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

Configuration change to auth_service: raise ACCOUNT_LOCKOUT_THRESHOLD from 5 to 10 failed login attempts in the same 5-minute window. Effective immediately, no code review required. This reduces the rate of legitimate collateral lockouts while still enforcing account protection against brute force. Revert if collateral damage is excessive (Dormouse reports >5% legitimate-user lockouts); accept otherwise.

**Acceptance:**
- ACCOUNT_LOCKOUT_THRESHOLD value changed from 5 to 10 in auth_service configuration
- Hotfix deployed to production
- Dormouse confirms new threshold is in effect (observes lockout events with >5 failures in logs)

**Risk:**

If threshold is too high (10 attempts), collateral-locked legitimate users increase; if too low, attack resumes. Monitor carefully for first 15 minutes post-deployment.
