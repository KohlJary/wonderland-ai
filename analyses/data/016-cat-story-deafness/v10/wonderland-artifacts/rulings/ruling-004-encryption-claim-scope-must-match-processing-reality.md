## Ruling 004: Encryption claim scope must match processing reality

**Severity:** high
**Domain:** privacy
**Source:** ADR-001 (plaintext external processing) + story-004 (Sofia's privacy expectation) + Tweedledee's implementation dependency

**Citation:**

GDPR Art. 13 (transparency of processing); GDPR Art. 32 (security of processing); FTC Unfair or Deceptive Acts or Practices (16 CFR § 255) — claims about encryption are security claims and must be accurate to what is actually implemented. CWE-200: Exposure of Sensitive Information to an Unauthorized Actor (the risk created if claims overstate protection).

**Finding:**

ADR-001's commitment to plaintext external translation means Sofia's input transits unencrypted to a third-party processor. The signup flow cannot claim 'end-to-end encryption' or 'encrypted messages' or any language implying the processing system cannot read her input. Claims that overstate protection are deceptive under FTC standards and violate GDPR transparency obligations. Sofia has a regulatory right to know her data is processed in plaintext; the system has a regulatory obligation to tell her.

**Required Remediation:**

The signup flow must disclose, in plain language, that (1) messages sent for translation are processed in plaintext by an external service, (2) the external service can read the plaintext, (3) transit to the external service is encrypted (TLS) but the message itself is not encrypted end-to-end, (4) the external service is [name the processor and jurisdiction], (5) Sofia can disable translation if she does not accept this processing. The disclosure must appear before signup is complete, not buried in Terms of Service. The language must match what ADR-001 actually implements — no hedging, no implication that encryption happens at a layer it does not.

**Acceptance Criteria:**
- Signup flow contains explicit disclosure of plaintext processing before account creation is confirmed
- The disclosure names the external processor and its jurisdiction
- The disclosure states plainly that the processor can read the plaintext
- The disclosure does not use language suggesting end-to-end encryption, message encryption, or encryption beyond TLS
- User has option to disable translation at signup time
- Caterpillar's review confirms the disclosure language matches the implementation

**Residual Risk:**

Users may still misunderstand the disclosure or make signup choices they later regret. This is mitigated by the plainness of the language and the opt-out at signup; it is not eliminated. The residual risk is acceptable — the system has discharged its transparency obligation.

**Compliance Implications:**

GDPR Art. 13 (right to be informed of data processing); GDPR Art. 32 (security obligations); California CCPA § 1798.100 (consumer right to know what personal information is collected); FTC Standards on encryption claims (Endorsements & Testimonials, 16 CFR Part 255). This ruling ensures compliance across these frameworks.

**Audit Reference:**

Queen ruling on ADR-001 plaintext processing scope. Signup disclosure language will be auditable in the implementation artifact and Dormouse observability logs (to confirm disclosure is presented to all users).
