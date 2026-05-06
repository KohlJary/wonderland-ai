## Ticket 013: Extend user account lockout threshold from 5 to 10 failed attempts, effective immediately

**Sources:** ruling/rate-limit-login-endpoint-to-halt-credential-stuffing-attack, ruling/extend-user-account-lockout-window-from-5-failed-attempts-to-10-effective-immediately
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 15 minutes, 95% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

Configuration hotfix to auth_service: change LOCKOUT_THRESHOLD from 5 to 10 failed login attempts per Queen ruling 001-extend-lockout-window. This is a single-line change to a config constant. Ship as a hotfix and deploy immediately; do not wait for rate-limit implementation. Acceptance: LOCKOUT_THRESHOLD reads 10 in the live service; accounts require 10 failed attempts before lockout instead of 5.

**Acceptance:**
- Config change deployed to production within 15 minutes
- New lockout threshold (10 attempts) is live and enforced on the /login endpoint
- Verification: test accounts confirm lockout occurs at exactly 10 failed attempts, not 5

**Risk:**

None. Single-line config change, no logic modifications. If the change breaks, rollback is trivial (revert the line).
