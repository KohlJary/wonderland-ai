## Observation 018: Scope sequencing misalignment: Queen's three rulings lock v1 requirements; observability contract not yet finalized; implementation revision must precede Caterpillar's gate

**Type:** incident
**Severity:** sev2
**Time window:** 2026-05-05T16:00:00Z — 2026-05-05T18:00:00Z

**Symptom:**

Queen issued three rulings specifying v1-blocking observability, distributed-IP defense, and password-reset escape hatch requirements. Simultaneously, implementation shipped without these constraints reflected in code. Caterpillar's review verdict (change-required) gates on observability and escape hatches. However, Dormouse's observability contract (ticket #11, referenced multiple times in thread) has not been published. Tweedles cannot implement observability hooks against an unspecified contract. Cat's architecture must confirm email-based rate-limiting is feasible and password-reset namespace is isolatable. The correct sequence (contract → implementation → review) is inverted; implementation is already in production, contract is still pending, review cannot gate effectively. This creates a window where production is running code that violates Queen's rulings, and compliance work (breach-notification) cannot proceed without observability hooks that do not yet exist.

**Affected scope:**

All v1 completion work blocked pending contract clarification. Breach-notification obligation cannot be executed until observability contract is locked and implementation is revised to emit observable events for successful logins during attack window.

**Evidence:**
- Queen ruling #3: 'production telemetry required before v1 ship' (issued 2026-05-05 ~18:00 UTC, implementation shipped earlier same day)
- Dormouse ticket #11 (observability contract): created, not yet resolved
- Caterpillar change-required verdict: gates on observability and escape hatches
- Hatter: six test scenarios specify observability acceptance criteria; current code does not satisfy scenarios #1, #2, #3, #4, #5, #6
- Alice: four user stories require observability instrumentation (breach-notification messaging requires knowing which credentials succeeded)

**Probable domain:** architecture, observability, compliance

**Routed to:** dodo
