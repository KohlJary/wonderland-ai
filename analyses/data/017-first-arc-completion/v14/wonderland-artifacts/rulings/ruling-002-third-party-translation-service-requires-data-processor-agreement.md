## Ruling 002: Third-party translation service requires data processor agreement

**Severity:** high
**Domain:** compliance
**Source:** proposal (adr: hub-model-translation)

**Citation:**

GDPR Art. 28 (processor obligations); Art. 28(3) (standard contractual clauses or approved adequacy decision); Art. 32 (security); Art. 35 (DPIA for overseas transfer). Specifically, if the translation service is located outside the EU/EEA, Art. 44-50 (transfers outside the EEA) also apply.

**Finding:**

The Cat's proposal correctly identifies that translations will be processed by a third party (he names no vendor, but the architecture assumes one). Under GDPR Art. 28, any third party that processes personal data on your behalf is a 'processor,' and you cannot use a processor without a written contract that meets Art. 28(3)'s requirements. The contract must specify: (1) subject matter and duration of processing; (2) nature and purpose of processing; (3) types of personal data; (4) categories of data subjects; (5) obligations and rights of the controller. Additionally, if the processor is outside the EU/EEA, you must have a lawful mechanism for the transfer (Standard Contractual Clauses, Binding Corporate Rules, or an adequacy decision). Shipping v1 without this contract in place means the application violates Art. 28 from day one.

**Required Remediation:**

Before the Tweedles implement the translation integration: (1) Select a specific translation service (e.g., Google Translate, DeepL, or self-hosted model). (2) If third-party: obtain the service's data processing addendum (DPA) or processor agreement. If the service does not offer one, you cannot use it (the service operator would need to enter a written contract with you per Art. 28(3)). (3) If the service is outside the EU/EEA: confirm the service has Standard Contractual Clauses or another lawful transfer mechanism in place. (4) Document the processor relationship in your compliance map: service name, location, processing scope (which user data, in what conditions), and the contract reference. (5) If you use a self-hosted model: no processor agreement is needed, but you own the security obligations under Art. 32 (encryption in transit and at rest, access controls, etc.). The Tweedles' implementation must reflect whichever choice is made.

**Acceptance Criteria:**
- Translation service vendor is named in the ADR or an implementation ticket
- If third-party: the data processing addendum is obtained and filed in compliance artifacts
- If third-party and outside EU/EEA: Standard Contractual Clauses or equivalent transfer mechanism is documented
- The compliance map includes a processor entry naming the vendor and the scope of processing
- The Tweedles' implementation does not call the translation service until the contract is in place

**Residual Risk:**

Even with a DPA in place, the third-party service may suffer a breach. This risk cannot be eliminated; the mitigation is to (1) select a service with strong security credentials, (2) monitor the service's security advisories, (3) include breach notification clauses in the DPA, and (4) keep only the minimum data necessary in transit to the translation service (do not send unnecessary metadata). The residual risk is accepted once the processor agreement is in place.

**Compliance Implications:**

GDPR Art. 28 (Processor); Art. 28(3)(c) (DPA requirements); Art. 44-50 (International Transfers); Art. 33 (Breach Notification to the processor, who must notify you). This is a compliance loading-path item: cannot proceed without it.

**Audit Reference:**

Ruling: scoping/processor-agreement-translation. Evidence: processor DPA, compliance map entry, transfer mechanism documentation.
