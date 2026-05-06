## Ruling 011: Post-incident threat-model update is mandatory; current threat model did not account for credential-stuffing attack class

**Severity:** high
**Domain:** authentication
**Source:** incident pattern; observation from Dormouse; test scenarios from Hatter

**Citation:**

OWASP A01:2021 Broken Access Control; NIST SP 800-63-3 Authentication and Lifecycle Management; incident fact: this attack succeeds because the threat model assumed that /login endpoint is rate-limited by default. It is not. The threat model was aspirational, not actual.

**Finding:**

The team has a threat model (exists in the Threat Garden, versioned with ADR-001). That threat model does not enumerate credential-stuffing attacks as a threat to the authentication service. This is a gap. The attack materialized exactly as the Hatter's scenarios predicted (high-volume, distinct-username, single-source-IP), which means the Hatter's attack methodology is sound but the team's threat model was not aligned with his methodology. Threat models that do not match the attack surface are not threat models; they are wishful thinking. This gap must be resolved before the incident is considered operationally closed.

**Required Remediation:**

Cheshire Cat must convene a threat-model update meeting (within 48 hours of incident stabilization) with Dormouse (production telemetry), Hatter (adversarial scenarios), Tweedles (implementation constraints), and myself (compliance implications). The meeting outcome is a revised threat model that includes: (1) credential-stuffing as a named threat, with attack vectors (IP-based, User-Agent-based, distributed/botnet-based), (2) mitigations ranked by effectiveness and cost (rate-limiting, MFA, CAPTCHA, behavioral detection), (3) a residual-risk statement on which attack variants are *not* defended against and why. The revised threat model becomes the canonical source for what the team defends against and what is accepted as residual risk.

**Acceptance Criteria:**
- Revised threat model is published to the Threat Garden (artifact location: `.wonderland/architecture/threat-models/v2-post-credential-stuffing/`)
- Threat model enumerates at least three credential-stuffing attack variants (IP-based, User-Agent-rotation-based, distributed/botnet-based) with attack surface and mitigation for each
- For each mitigation, the threat model names the residual risk (e.g., 'IP-based rate-limit accepted risk: 5-10% false-positive rate on shared corporate networks')
- Cat's ADR is updated to reference the revised threat model; the ADR names which architectural decisions are now required vs optional based on the new threat model

**Residual Risk:**

Threat-model updates are forward-looking; they do not prevent the attack that just happened, they prevent the *next* variant. The team may discover during the update meeting that mitigating distributed/botnet-based credential-stuffing (scenario #5) is outside scope or requires architectural changes deferred to v2. That is acceptable if explicitly documented. What is not acceptable is shipping without the updated threat model and then being surprised when variant attacks succeed.

**Compliance Implications:**

GDPR Recital 83 requires that organizations demonstrate that they have considered the threats to personal data and implemented appropriate safeguards. A threat model that did not account for credential-stuffing — a known, widespread threat — is evidence of insufficient due diligence. The updated threat model is the documentation that due diligence has occurred.

**Audit Reference:**

Threat Garden entry: 'Credential-stuffing attack threat-model gap / First identified: thread 47 (this thread) / Remediation: post-incident threat-model update + ADR revision / Status: scheduled, not yet completed.'
