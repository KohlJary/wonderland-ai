## Ruling 012: Password-reset endpoint rate-limiting — instrumentation clarity required before v1 completion

**Severity:** high
**Domain:** authentication
**Source:** Dormouse observation gap + Hatter scenario 5 + Rabbit dependency clarification

**Citation:**

OWASP A07:2021 Identification and Authentication Failures; OWASP A04:2021 Insecure Design (account-recovery flows must not become attack vectors); incident-response requirement: a legitimate user locked out of their account must be able to self-recover without becoming a secondary attack surface

**Finding:**

The /password-reset endpoint either (a) does not exist yet, (b) shares rate-limit logic with /login and will therefore lock out users trying to self-recover from credential compromise during an active attack, or (c) has no rate-limiting and becomes a secondary credential-stuffing vector (reset-spam to lock accounts, then takeover). Without knowing which of these is true, the team cannot implement rate-limiting correctly, and the team cannot commit to the Queen's ruling on escape hatches.

**Required Remediation:**

The Tweedles will immediately confirm: (1) does /password-reset endpoint exist in production? (2) if yes, what rate-limiting policy does it currently have? (3) if it shares rate-limit logic with /login, what is the current behavior when a locked-out user attempts password reset? The answer determines whether /password-reset must be re-architected (most likely: separate rate-limit namespace with higher threshold for reset flows) or already complies with the Queen's escape-hatch ruling. This confirmation must happen before implementation resumes, not after.

**Acceptance Criteria:**
- Tweedles confirm /password-reset endpoint existence and current rate-limit policy (if any)
- If /password-reset shares rate-limit logic with /login, Tweedles propose separate rate-limit policy for reset flows
- If /password-reset has no rate-limiting, Tweedles propose appropriate rate-limit thresholds for reset flows (higher than login flows to allow self-recovery)
- Dormouse confirms observability can distinguish reset-flow rate-limit events from login-flow events in telemetry
- Caterpillar reviews the final /password-reset rate-limiting logic for escape-hatch correctness (locked users can self-recover without triggering additional rate-limit)

**Residual Risk:**

If /password-reset does not yet exist, this work becomes a v1 dependency and delays mitigation completion. This is acceptable; shipping a complete defense is better than shipping mitigation that creates secondary attack vectors.

**Compliance Implications:**

OWASP design principle: recovery flows must not become attack surfaces. The rate-limiting policy for /password-reset must be auditable; the contract specification is the artifact that makes this testable.

**Audit Reference:**

Password-reset endpoint scope confirmation; Tweedles implementation contract note; Dormouse telemetry specification for reset-flow events
