## Ruling 002: Third-party translation service requires Data Processing Agreement; data residency depends on vendor location

**Severity:** high
**Domain:** data-handling
**Source:** architectural proposal from Cheshire Cat; GDPR Art. 28 processing obligations

**Citation:**

GDPR Art. 28 (Processor obligations); GDPR Art. 44-50 (Transfer restrictions); GDPR Art. 6 (lawfulness of processing)

**Finding:**

The Cat's proposal uses an external translation vendor (Google Translate, DeepL, etc.). Under GDPR Art. 28, any external service that processes personal data (message text, user identity, conversation metadata) is a Data Processor, and the system is the Data Controller. A Data Processing Agreement (DPA) is mandatory before data flows to the processor. Additionally, if the processor is located outside the EU/EEA and there is no adequacy decision (e.g., US vendors under the former Privacy Shield or current Data Privacy Framework), transfers are restricted under GDPR Art. 44-50 and require additional safeguards (Standard Contractual Clauses, Binding Corporate Rules, or approved derogations). The current proposal does not specify the vendor or address these requirements.

**Required Remediation:**

Before any translation service integration: (1) select a specific vendor (Google Translate, DeepL, AWS Translate, etc.); (2) verify the vendor's data residency and whether they are located in an adequacy jurisdiction; (3) for non-EU vendors, obtain or draft a Data Processing Agreement that includes Standard Contractual Clauses (SCCs) if required; (4) document the DPA execution status and the transfer mechanism (SCC reference, adequacy decision reference, or approved derogation); (5) add the vendor to the system's vendor register (artifact to be created). Only when the DPA is executed can message data flow to the translation service.

**Acceptance Criteria:**
- Translation vendor is named (e.g., 'DeepL' or 'Google Translate')
- Vendor data residency is documented (e.g., 'DeepL EU, data stays in EU'; 'Google US, adequacy decision applies')
- If vendor is outside EU/EEA: DPA with SCCs is drafted, reviewed by legal, and signed before implementation
- If vendor is within EU/EEA: DPA is confirmed in writing (vendor website, contract, or standard agreement); reference documented
- Vendor register entry created: vendor name, data residency, DPA status, contact info for breach notification
- Translation service call logs include vendor name, timestamp, data volume (message character count), response time — for audit trail

**Residual Risk:**

US vendors under Data Privacy Framework have weaker protections than EU data protection law; the DPA with SCCs is the mitigation. If the vendor is acquired or their data-handling practices change, the DPA may need renegotiation. Review vendor status annually.

**Compliance Implications:**

GDPR Art. 28 (Processor obligations); GDPR Art. 44-50 (Transfer restrictions); GDPR Art. 6(1) (lawfulness of processing). Absence of a DPA is a compliance violation; message data cannot flow to the vendor legally without it.

**Audit Reference:**

Compliance Map entry: 'GDPR Art. 28 — processor agreement'; Threat Garden entry: 'third-party data processing risk.'
