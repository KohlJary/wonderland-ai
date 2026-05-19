## Ruling 006: Markdown library must be actively maintained and have audit trail for security patches

**GUID:** 01KRXWVM6YSTG7BJ3542BY3235
**Severity:** high
**Domain:** dependencies
**Source:** story (Markdown preview renderer component) with XSS-handling implications flagged by Alice

**Citation:**

OWASP A06:2021 Vulnerable and Outdated Components; CWE-1035 (vulnerable dependency in third-party code); common markdown library vulnerabilities include HTML injection through unescaped HTML passthrough modes

**Finding:**

The markdown library the team selects will handle user-provided markdown input and emit HTML. If the library is unmaintained, has known unpatched vulnerabilities, or does not sanitize HTML by default, Kohl's note content could be used to inject malicious scripts into her own editor (self-XSS) or, if notes are ever shared, into other users' browsers. Alice flagged this correctly: markdown libraries typically sanitize HTML, but 'typically' is not 'always,' and unmaintained libraries accumulate CVEs. The team must choose a library with an explicit security posture, not assume safety from popularity.

**Required Remediation:**

Before the Tweedles implement the preview component, the team must select a markdown library that: (1) is actively maintained (releases within the last 6 months), (2) has a disclosed security policy or vulnerability response history, (3) sanitizes HTML by default (no `html: true` or equivalent flag enabled), (4) is listed in a dependency scanner (npm audit, Snyk, etc.) and produces no critical/high CVEs. Document the library choice in the ADR with a security note explaining why this library satisfies the constraints.

**Acceptance Criteria:**
- Markdown library is named in the ADR with explicit rationale for the security choice
- npm audit or equivalent produces no critical/high severity vulnerabilities for the chosen library at time of implementation
- Library documentation confirms HTML sanitization is default behavior (not opt-in)
- Tweedles' implementation does not override sanitization settings (e.g., no dangerouslySetInnerHTML + custom markdown parsing)

**Residual Risk:**

Zero-day vulnerabilities in the markdown library are possible but not preventable through library selection alone—they are mitigated by dependency scanning in CI/CD and Dormouse observation of production behavior. The ruling does not require the team to audit the library's source code or guarantee its security, only to choose a library with a professional security posture and a documented way to receive patches when needed.

**Compliance Implications:**

If this application ever expands to multi-user note sharing, XSS vulnerabilities become compliance concerns under OWASP ASVS 5.3.3 (output encoding). Locking down the library choice now prevents a problematic retrofit later.

**Audit Reference:**

Dependency selection and security audit trail for markdown library choice, recorded in the ADR.
