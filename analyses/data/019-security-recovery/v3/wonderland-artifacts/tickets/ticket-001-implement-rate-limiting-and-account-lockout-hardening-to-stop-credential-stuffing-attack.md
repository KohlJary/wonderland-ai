## Ticket 001: Implement rate-limiting and account-lockout hardening to stop credential-stuffing attack

**Sources:** observation: Anomalous auth-failure spike from single IP — possible credential stuffing in progress
**Owner:** Tweedledee & Tweedledum
**Tier:** v1
**Estimate:** 2–3 hours, 75% confident (implementation is straightforward; contract negotiation with Cat may extend by 30min)
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: Queen's ruling on rate-limit shape and lockout threshold, Cat's architectural review of integration point

**Description:**

Add rate-limiting and lockout-policy enforcement to the auth service to stop the credential-stuffing attack in progress. The codebase already tracks FailedAttempt; the gaps are (1) per-IP rate limiting on /login, (2) account lockout at configurable threshold, (3) per-IP request gating. Implement as new src/auth/rate_limit.py module with RateLimiter class. Integrate into AuthService.login via middleware chain or direct call — Cat will advise on cleanest surface. Extend tests/test_auth.py with rate-limit and lockout test scenarios. Do not wait for full architectural consensus; Pair Protocol §V applies — ship a working contract and negotiate details in-flight if needed. Queen's ruling on mitigation shape (per-IP? per-email? both?) and lockout threshold will arrive separately and may require adjustment; plan for a 15–30min pivot.

**Acceptance:**
- Rate limiting is active on /login endpoint; requests from same IP beyond threshold within time window are rejected with 429 before auth logic runs
- Account lockout engages after N failed attempts (initially 5, subject to Queen's ruling); locked accounts cannot log in until unlock or timeout
- FailedAttempt tracking is used to feed both per-IP and per-account signals
- New test scenarios in tests/test_auth.py cover: rate-limit rejection, account lockout, lockout recovery, cross-account attack simulation
- Code diff ships cleanly against existing auth service; no breaking changes to existing endpoints or session middleware

**Risk:**

Rate-limit implementation could block legitimate users if threshold is too aggressive; lockout policy needs Queen's input before we fully commit the threshold. Plan for 1–2 adjustment cycles in the next 15min as Queen rules.
