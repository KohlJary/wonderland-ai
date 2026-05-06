## Observation 019: Credential-stuffing mitigation v1: three user-facing requirements remain unconfirmed in review

**Type:** incident
**Severity:** sev2
**Time window:** 2026-05-05T14:23:00Z — ongoing

**Symptom:**

Caterpillar's review surfaces three blocking issues (observability, escape hatches, test coverage) but does not confirm whether implementation satisfies Queen's three rulings or Hatter's six test scenarios. Specifically: (1) no confirmation that successful-login events are instrumented for breach-notification work (Queen ruling #3 requires this as v1 gate); (2) no clarity on /password-reset rate-limit isolation (Queen ruling #2 requires separate policy, currently undefined); (3) no confirmation that Hatter's scenarios are covered by test suite, particularly distributed-IP bypass, shared-IP false positives, and password-reset recovery flow. Implementation shipped without waiting for observability contract (Dormouse ticket #11), creating gap between what Queen ruled as v1-blocking and what review confirms is present.

**Affected scope:**

User-facing breach-notification capability (which users can be notified about compromise), password-reset recovery flow (whether locked users can self-recover), test coverage for distributed and edge-case attack scenarios.

**Evidence:**
- Caterpillar review summary: three blocking categories (observability, escapes, coverage) with no resolution criteria
- Queen ruling #3: 'production telemetry required before v1 ship' — observability instrumentation absent per Caterpillar finding
- Queen ruling #2: '/password-reset endpoint rate-limiting must have separate policy' — scope undefined per review
- Hatter test scenarios #3, #5, #6: legitimate-user false positives, password-reset escape, observability instrumentation — coverage status unclear
- Dormouse observation: 'scope sequencing misalignment: Queen's three rulings lock v1 requirements; observability contract not yet finalized'

**Probable domain:** backend

**Routed to:** caterpillar
