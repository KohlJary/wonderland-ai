## Ticket 003: Caterpillar: review rate-limiting and lockout implementation

**Sources:** implementation: rate-limiting and lockout hardening
**Owner:** Caterpillar
**Tier:** v1
**Estimate:** 1–1.5 hours, 70% confident (code review of rate-limit module and integration points)
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: implementation: rate-limiting and lockout hardening
- Soft: —

**Description:**

Review the Tweedles' implementation of rate-limiting and account-lockout mitigation against the incident response ticket. Focus on: (1) RateLimiter class interface and correctness, (2) integration with AuthService.login (does it compose cleanly with existing auth flow?), (3) FailedAttempt schema usage (are we tracking the right signals?), (4) test coverage (do new test scenarios lock in the behavior?), (5) edge cases (what happens when rate-limit expires? when lockout timeout fires? when a user resets their password?). Code quality bar is normal; speed-pressure exceptions are allowed but noted. Approval required before the mitigation is considered live.

**Acceptance:**
- Review is published as a git_diff-referenced artifact
- All substantive concerns are addressed before approval
- Approval is explicit; implementation is approved or conditional-pending-changes

**Risk:**

Caterpillar review can take time; plan for 30–60min if significant changes are needed. Pair Protocol §V applies — the implementation can stay live while changes are negotiated if the current behavior is net-positive.
