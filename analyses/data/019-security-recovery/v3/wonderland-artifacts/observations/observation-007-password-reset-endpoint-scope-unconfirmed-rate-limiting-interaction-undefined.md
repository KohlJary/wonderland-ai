## Observation 007: Password-reset endpoint scope unconfirmed; rate-limiting interaction undefined.

**Type:** anomaly
**Severity:** sev2
**Time window:** 2026-05-05T15:12:00Z — ongoing

**Symptom:**

The implementation does not document whether /password-reset exists, whether it shares rate-limiting logic with /login, or how it behaves when a user is locked out. Queen's ruling #2 requires that password-reset must not be rate-limited in a way that prevents legitimate password recovery. The current implementation cannot confirm compliance with this ruling because the interaction is undefined.

**Affected scope:**

Auth service. Users locked out by the attack cannot confirm whether they can self-recover via password-reset. If /password-reset shares rate-limiting with /login, they cannot. If it does not exist, they cannot.

**Evidence:**
- Tweedledee implementation artifact does not mention /password-reset
- Rabbit ticket slug=confirm-password-reset-endpoint-scope-and-lockout-interaction remains open
- Queen's ruling #2 requires resolution of this interaction before v1 completion
- Hatter test scenario #5 (lockout-escape-hatch) — implementation status unclear

**Probable domain:** backend

**Routed to:** tweedledee
