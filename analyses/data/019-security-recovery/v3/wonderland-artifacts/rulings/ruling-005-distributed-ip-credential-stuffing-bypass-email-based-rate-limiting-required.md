## Ruling 005: Distributed-IP credential-stuffing bypass — email-based rate-limiting required

**Severity:** high
**Domain:** authentication
**Source:** test_scenario from Mad Hatter (silent-wrongness-rate-limit-bypass-via-distributed-attack-across-many-ips-on-same-email)

**Citation:**

OWASP A07:2021 Identification and Authentication Failures; CWE-307 Improper Restriction of Rendered UI Layers or Frames; threat model: credential-stuffing attack patterns show distributed-IP escalation when single-IP limiting is deployed without secondary defense.

**Finding:**

Per-IP rate-limiting stops the current single-source attack but does not defend against the same attacker or botnet iterating across different IPs while targeting the same email address. This is a known escalation pattern in commodity credential-stuffing tooling; attackers will pivot to it within hours of detecting per-IP limiting. Shipping per-IP limiting without email-based secondary defense leaves the attack surface open at the email layer. Users whose emails are in the leaked-credentials list will experience repeated attack waves.

**Required Remediation:**

Implement email-based rate-limiting on the /login endpoint: track failed login attempts per email address (in addition to per-IP limiting), enforce separate rate-limit threshold per email (recommendation: 10 failed attempts per email per 24-hour window), and trigger account lockout or CAPTCHA challenge at email threshold regardless of IP source. The email-based limit must survive IP rotation.

**Acceptance Criteria:**
- Failed login attempts are tracked and aggregated per email address in addition to per-IP aggregation
- Rate-limit enforcement logic triggers for email-based threshold independently of IP-based threshold (AND logic, not OR)
- Integration test confirms that a distributed attack across 5+ distinct IPs targeting the same email triggers email-based rate-limit before succeeding
- Hatter's scenario 'silent-wrongness-rate-limit-bypass-via-distributed-attack-across-many-ips-on-same-email' passes

**Residual Risk:**

Email-based rate-limiting increases false-positive surface: legitimate users sharing corporate networks (where multiple employees log in from the same IP) may trigger IP-based limits together; legitimate users with typos in their email may trigger email-based limits. These are acceptable given the severity of the attack surface. Mitigation: clear per-email-address rate-limit state on successful password reset (see ruling: lockout-escape-hatch).

**Compliance Implications:**

None directly; this is a threat-model defense, not a compliance requirement. However, if the attack succeeds and credentials are compromised, breach-notification obligations (see separate ruling) are triggered. Email-based rate-limiting reduces breach likelihood and thus breach-notification scope.

**Audit Reference:**

incident-response thread: email-based rate-limit implementation; post-deployment validation in production telemetry
