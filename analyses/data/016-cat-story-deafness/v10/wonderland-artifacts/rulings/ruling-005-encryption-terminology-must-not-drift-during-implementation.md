## Ruling 005: Encryption terminology must not drift during implementation

**Severity:** medium
**Domain:** data-handling
**Source:** ADR-001 + Tweedledee's implementation dependency

**Citation:**

GDPR Art. 5(1)(a) (lawfulness, fairness, transparency); CWE-200 (exposure of sensitive information through deceptive claims).

**Finding:**

Tweedledee will implement signup; during implementation, there is a natural temptation to soften the plaintext disclosure or to use language like 'secure processing' or 'encrypted by default' that is technically true (TLS exists) but implies end-to-end protection that does not exist. This is semantic drift into deception. The plaintext processing is the material fact; everything else is context.

**Required Remediation:**

Tweedledee's implementation must use the exact disclosure language approved by the Queen and Caterpillar. No variation. No 'secure processing' as a substitute for 'plaintext processing.' If Tweedledee finds the disclosure language awkward to implement, the correct response is to surface the awkwardness as a `concern`, not to reword unilaterally.

**Acceptance Criteria:**
- Signup disclosure language appears verbatim in the implementation (parameterized only by processor name/jurisdiction)
- Caterpillar's review confirms no semantic drift in the disclosure phrasing
- Dormouse observability confirms 100% of signups present the disclosure

**Residual Risk:**

None that materially affects the ruling. The risk is implementation discipline, which Caterpillar's review catches.

**Audit Reference:**

Supports the primary ruling on encryption scope. Audit trail will include both the approved disclosure language and evidence it was presented.
