## Ruling 003: Authentication must use encrypted transport and hashed password storage

**Severity:** high
**Domain:** authentication
**Source:** proposal from Cheshire Cat (basic auth mentioned in directive)

**Citation:**

OWASP Top 10 A02:2021 Cryptographic Failures; CWE-522 Insufficiently Protected Credentials; GDPR Article 32(1)(b) (encryption and pseudonymization).

**Finding:**

The directive mentions 'basic auth' without specifying the implementation. Basic HTTP auth (RFC 7617) sends credentials in Base64 encoding, which is not encryption—it is obfuscation. If the transport layer is not TLS, credentials are plaintext over the wire. If password storage is plaintext or insufficiently hashed, credentials are plaintext at rest. Both are exploitable.

**Required Remediation:**

All authentication traffic must occur over TLS 1.2 or higher. Password hashing must use a modern, slow hash function (bcrypt, Argon2, scrypt with appropriate work factors). Passwords must never be stored plaintext, logged, or transmitted outside the TLS tunnel. The ADR or a separate authentication specification must document these requirements before the Tweedles implement.

**Acceptance Criteria:**
- All auth endpoints are TLS-only; non-TLS requests are rejected
- Passwords are hashed using bcrypt (cost ≥ 12) or Argon2 (t ≥ 2, m ≥ 65536) at storage time
- Caterpillar's review confirms no plaintext passwords in code, logs, or error messages

**Residual Risk:**

None material; these are industry baseline, not edge-case mitigations.

**Compliance Implications:**

GDPR Article 32(1)(b) requires encryption and pseudonymization of personal data. Password credentials are personal data; encryption at rest and in transit is mandatory.

**Audit Reference:**

Ruling #[authentication-basics]; blocks Tweedledee and Tweedledum implementation until ADR or auth spec clarifies these requirements; Dormouse will verify no unencrypted auth traffic reaches production.
