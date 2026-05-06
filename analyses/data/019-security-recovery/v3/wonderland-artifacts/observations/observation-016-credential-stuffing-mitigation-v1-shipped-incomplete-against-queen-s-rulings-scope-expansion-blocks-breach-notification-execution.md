## Observation 016: Credential-stuffing mitigation v1 shipped incomplete against Queen's rulings; scope expansion blocks breach-notification execution

**Type:** incident
**Severity:** sev1
**Time window:** 2026-05-05T14:23:00Z — 2026-05-05T17:15:00Z

**Symptom:**

Rate-limiting and account-lockout implementation deployed to production. Attack is mitigated (compromised attempts dropped from 47 to 3 per minute as of 17:15 UTC, no new lockouts triggered in last 60 minutes). However, three Queen rulings now define v1 requirements that the shipped code does not satisfy: (1) distributed-IP defense requires email-based rate-limiting (current code is IP-based only), (2) password-reset endpoint must have separate rate-limit policy (not enforced in current namespace design), (3) breach-notification observability requires successful-login event instrumentation (current code emits only failure telemetry). The rulings are v1-blocking; the implementation is incomplete against all three.

**Affected scope:**

All authenticated users attempting login during attack window (14:23–17:15 UTC). Distributed-attack surface unaddressed. Breach-notification obligation cannot be executed. Password-reset escape hatch unspecified for future work.

**Evidence:**
- Queen ruling #1: 'Distributed-IP credential-stuffing bypass — email-based rate-limiting required'
- Queen ruling #2: 'Password-reset endpoint rate-limiting — must not lockout legitimate password-recovery flow'
- Queen ruling #3: 'Rate-limit and lockout observability — production telemetry required before v1 ship'
- Metrics: attack rate 47 req/min → 3 req/min (14:23–17:15), decline consistent with per-email lockout engagement, not per-IP rate-limit
- Hatter scenarios #4, #5, #6 specify observability requirements current code does not emit
- Caterpillar review verdict: change-required (observability, escape hatches)

**Probable domain:** architecture, implementation, observability

**Routed to:** cheshire_cat
