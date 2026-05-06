## Observation 010: Password-reset endpoint: rate-limiting interaction undefined; scope confirmation pending.

**Type:** anomaly
**Severity:** sev2
**Time window:** 2026-05-05T14:23:00Z — ongoing

**Symptom:**

The Queen's ruling #2 (password-reset isolation) assumes /password-reset endpoint exists and rules that it must not be lockout-isolated by the per-email account lockout policy. The Hatter's scenario #5 confirms this seam: a user locked out by the attack will attempt password reset; if /password-reset shares the per-email lockout counter, the reset attempt will fail. However, the implementation does not clarify whether /password-reset exists, whether it is in-scope for v1, or how it interacts with the rate-limiting and lockout controls. This is a user-experience blocker: if /password-reset shares the lockout state and a user tries to self-recover during the attack, they will be denied both login and password-reset. The Rabbit's ticket list includes 'confirm-password-reset-endpoint-scope-and-lockout-interaction', but I cannot observe the outcome of that confirmation in the current state.

**Affected scope:**

/password-reset endpoint (if it exists); account-lockout policy interaction; user recovery flows during attack

**Evidence:**
- Queen's ruling #2: 'Password-reset endpoint rate-limiting — must not lockout legitimate password-recovery flow'
- Hatter's scenario #5: 'Lockout escape hatch — legitimate password-reset flow must not be rate-limited'
- src/auth/account_lockout.py: lockout state is per-email, checked on /login; no mention of /password-reset interaction
- Rabbit's ticket: 'Confirm /password-reset endpoint scope and lockout interaction' (open, no resolution visible)

**Probable domain:** backend

**Routed to:** tweedledum
