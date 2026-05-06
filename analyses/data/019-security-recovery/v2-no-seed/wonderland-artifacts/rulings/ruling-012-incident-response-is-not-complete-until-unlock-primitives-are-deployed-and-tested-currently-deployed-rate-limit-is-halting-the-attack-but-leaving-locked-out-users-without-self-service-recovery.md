## Ruling 012: Incident response is not complete until unlock primitives are deployed and tested; currently-deployed rate-limit is halting the attack but leaving locked-out users without self-service recovery

**Severity:** high
**Domain:** authentication
**Source:** story from Alice; concern from Dormouse, Rabbit, Caterpillar; ADR-001 from Cheshire Cat

**Citation:**

OWASP A01:2021 Broken Access Control (authorization after authentication); CWE-640 Weak Password Recovery Mechanism; user harm principle: legitimate users are locked out; the system must provide them self-service recovery without support friction.

**Finding:**

The rate-limit enforcement stops the *attack*; it does not complete the *defense*. 47 legitimate users are now locked out, and their recovery path is either (a) wait 5 minutes for the lockout window to expire, or (b) contact support for manual unlock. Neither is acceptable for 'incident response is complete.' Alice's stories name what recovery means: 'regain access quickly without support friction.' The current state — rate-limit halting new attacks, lockout preventing brute force, but no unlock primitive — is operationally correct for stopping the bleeding. It is not correct for declaring the incident resolved to users. This is not a criticism of Tweedledum's implementation; the rate-limit logic is sound and necessary. This is a scope gate: incident response scope must include unlock primitives or user-facing recovery is incomplete.

**Required Remediation:**

Deploy account-recovery primitives sufficient for Alice's stories to be true: (1) email-based account unlock via time-limited token (issued on user request, valid for 15 minutes, one-time-use), (2) unlock endpoint that validates the token and sets account.locked = false, (3) client-side UX that presents 'Unlock Account' option on login failure and redirects locked-out users to unlock-email-request flow. The unlock must not require the password (which is compromised during credential-stuffing; see ADR-001); it must not be available to attackers (Cat's decoupling proposal). Email-token-based unlock satisfies both: users control the unlock by checking email, attackers cannot use the breached password to unlock. Cost estimate: 2-3 hours for Tweedles (email handler, token management, endpoint, UX), 1 hour for Caterpillar review, 30 minutes for Hatter scenario verification. This is v1 unlock; hardening (monitoring unlock-path abuse, rate-limiting unlock attempts) is fast-follow.

**Acceptance Criteria:**
- Unlock endpoint (/account/unlock) exists and accepts a token parameter
- Token validation works: token must be valid (correct hash), not expired (< 15 min old), and one-time (marked used after first validation)
- Account unlock sets account.locked = false and clears failed-login counter
- Client-side login-failed UX displays 'Unlock Account' button; clicking routes to email-request form
- Hatter's test scenario #1 (email-based unlock path) passes: user requests unlock, receives email within 30 seconds, clicks link, account is unlocked, can log back in
- End-to-end unlock takes < 5 minutes for user in normal email-delivery conditions (Alice's acceptance criterion: 'regain access within 5 minutes')

**Residual Risk:**

Email-based unlock introduces a new attack surface: if the attacker controls the user's email account, they can unlock the locked account without the password. This is accepted as a residual risk because (a) email account compromise is a higher-level threat (out of scope for this incident response), (b) it is explicitly documented as a residual risk, (c) post-incident hardening (SMS-based backup, security-question-based backup) can mitigate if this becomes a pattern. The unlock primitive as specified is sufficient for incident response and user recovery; it is not sufficient for long-term defense against email-account compromise.

**Compliance Implications:**

This is not directly a compliance requirement, but denial-of-service recovery (users locked out by the mitigation) is related to availability and resilience, which several frameworks (HIPAA, SOC 2, PCI DSS) require. Documenting that the system provides self-service recovery from DDoS-induced lockout is evidence of resilience design.

**Audit Reference:**

Threat Garden entry: 'Credential-stuffing attack (IP-based) / Mitigation: rate-limit + lockout + email-based unlock (v1 incident response) / User-impact residual: false-positive lockout on shared IPs (see Hatter scenario #4) / Remediation: monitor collateral-damage rate, consider CAPTCHA or account-verification as v1.1 enhancement / Status: unlock primitive pending deployment.'
