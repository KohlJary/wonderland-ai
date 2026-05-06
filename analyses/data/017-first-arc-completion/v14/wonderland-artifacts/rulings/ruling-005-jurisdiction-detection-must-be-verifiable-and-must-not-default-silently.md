## Ruling 005: Jurisdiction detection must be verifiable and must not default silently

**Severity:** high
**Domain:** privacy
**Source:** Cat's concern re: geo-scoped consent path + Queen's implicit assumption in model (1)

**Citation:**

GDPR applies to processing of personal data of EU residents regardless of where the controller is located (Art. 3). The system must correctly identify EU-resident users to apply the appropriate consent model. CWE-200 'Exposure of Sensitive Information to an Unauthorized Actor' applies if jurisdiction detection fails and non-EU users are incorrectly routed to GDPR flows, or EU users bypass GDPR flows.

**Finding:**

If the team chooses model (1) — geo-scoped consent — the system must reliably detect whether a user is in an EU jurisdiction. This detection is security-critical: a failure that misclassifies an EU user as non-EU and routes them to a non-consenting flow is a GDPR violation with user-harm consequences (personal data processed without lawful basis). The team has not yet specified how jurisdiction will be detected (IP geolocation? User self-report? Payment method locale? Auth system locale?). Each method has failure modes. IP geolocation can be spoofed or inaccurate. Self-report can be false. Without a clear method, implementation will drift into fragile heuristics.

**Required Remediation:**

If model (1) is chosen: (a) specify the jurisdiction-detection mechanism with explicit fallback behavior (e.g., 'if IP geolocation is ambiguous, treat as EU'); (b) do not default to non-EU implicitly — if jurisdiction is unknown, route to the more protective (EU) flow; (c) allow users to override their detected jurisdiction (e.g., 'I am outside the EU' checkbox) and log that override; (d) audit-log every jurisdiction determination at login, so compliance audits can verify correctness. If model (2) or (3) is chosen: this requirement does not apply, as consent is uniform.

**Acceptance Criteria:**
- Jurisdiction detection mechanism is named (IP geolocation / user self-report / other) with documented accuracy expectations
- Fallback behavior when detection is ambiguous is explicit (defaults to EU/protective if unknown)
- User can view and override detected jurisdiction in account settings
- Every login logs the detected jurisdiction, the detection mechanism used, and whether the user overrode it
- Audit trail is queryable by jurisdiction to verify the system correctly routed users pre-implementation

**Residual Risk:**

IP geolocation has inherent accuracy limitations (VPN usage, proxy services, border regions). The residual risk is that a user's jurisdiction is misdetected despite best efforts. This is defensible if: (1) the system defaults to the more protective flow (EU) when unsure; (2) users can override; (3) logs show the detection attempt and the reason for misclassification if discovered later. Document this as a known limitation and make it part of the compliance map.

**Compliance Implications:**

GDPR Article 3(1) extends GDPR to all processing of EU-resident data, regardless of where the system operates. Misrouting users due to failed jurisdiction detection is a violation. The compliance map must record the jurisdiction-detection strategy and its error rates (post-launch, use Dormouse observations to validate real-world accuracy).

**Audit Reference:**

Jurisdiction Detection Strategy (JDS-001): recording the detection mechanism, fallback behavior, override capability, and residual accuracy risk.
