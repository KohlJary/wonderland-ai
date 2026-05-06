## Observation 014: Credential-stuffing mitigation v1 incomplete against Queen's three new rulings; scope expansion requires contract clarification before implementation resumes

**Type:** incident
**Severity:** sev1
**Time window:** 2024-12-19T14:23:00Z — 2024-12-19T15:47:00Z

**Symptom:**

Tweedles shipped rate-limiting and account-lockout implementation (per prior `implementation` artifact). Queen issued three rulings subsequently: (1) distributed-IP defense requires email-based rate-limiting (not IP-based alone), (2) password-reset isolation must prevent lockout bypass, (3) observability instrumentation required before v1 ship to support breach-notification ruling. Current implementation satisfies none of these three. Scope expansion is real; implementation contract is incomplete.

**Affected scope:**

v1 mitigation scope, implementation contract, Queen's ruling execution surface

**Evidence:**
- Queen ruling slug=distributed-ip-credential-stuffing-bypass-email-based-rate-limiting-required (issued after Tweedles' implementation)
- Queen ruling slug=password-reset-endpoint-rate-limiting-must-not-lockout-legitimate-password-recovery-flow (issued after Tweedles' implementation)
- Queen ruling slug=rate-limit-and-lockout-observability-production-telemetry-required-before-v1-ship (issued after Tweedles' implementation)
- Tweedledee implementation artifact: IP-based rate-limiting only, no email-based, no observability hooks
- Dormouse observation slug=rate-limiting-and-account-lockout-implementation-deployed-observability-instrumentation-absent

**Probable domain:** architecture, implementation, security compliance

**Routed to:** white_rabbit
