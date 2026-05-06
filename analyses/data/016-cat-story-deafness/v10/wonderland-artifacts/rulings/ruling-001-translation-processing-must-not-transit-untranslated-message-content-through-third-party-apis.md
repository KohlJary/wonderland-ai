## Ruling 001: Translation processing must not transit untranslated message content through third-party APIs

**Severity:** critical
**Domain:** data-handling
**Source:** proposal from Cheshire Cat

**Citation:**

GDPR Article 28 (processor obligations); Article 32 (security of processing); Article 44 (transfers of personal data). Message content is personal data of EU consumers. Transfer to a third-party translation service (e.g., Google Translate API) without a signed Data Processing Agreement constitutes unlawful transfer and exposes the team to regulatory sanction.

**Finding:**

The ADR proposes 'cloud translation service (AWS Translate, Google Translate API)' as the load-bearing seam. This pattern sends untranslated user messages—personal data of EU consumers—to a third-party processor. Without a pre-existing Data Processing Agreement between the team's organization and the service provider, this transfer violates GDPR Article 44 (transfers must have adequate safeguards). The user has not consented to transfer to a third party; the story-based user expectation is translation *by the system*, not *through an external party*. Shipping this ADR as-written ships a GDPR breach.

**Required Remediation:**

The translation processing must occur either (a) in-house, using an open-source or self-hosted model (e.g., OpenNMT, Hugging Face transformers deployed on your infrastructure), or (b) via a third-party service *only if* a signed Data Processing Agreement exists and the service provider's sub-processor list does not include additional onward transfers. The team must make this choice and commit to it before the Tweedles implement. The choice is architectural (the Cat's domain); my ruling constrains the choices available to him.

**Acceptance Criteria:**
- The ADR revision names the translation processing location (in-house or specific third-party service with DPA)
- If third-party service: a signed Data Processing Agreement is on file before any untranslated message content transits through the service
- If in-house: the model provenance, training data residency, and operational overhead (latency, compute cost) are documented in the ADR

**Residual Risk:**

In-house translation models carry quality risk (accuracy of translation may be lower than commercial services) and operational risk (model requires ongoing updates as language use evolves). These are acceptable tradeoffs given the regulatory constraint; the team can optimize translation quality iteratively without legal exposure.

**Compliance Implications:**

GDPR Article 28 (data processor requirements); Article 32 (security of processing); Article 44 (international transfers). This ruling determines whether the system is compliant or non-compliant at v1 ship. Non-compliance at ship is a regulatory finding; compliance from the start is table stakes.

**Audit Reference:**

Ruling #[translation-data-residency]; blocks implementation until ADR revision is complete; Dormouse will verify telemetry shows no untranslated content transiting external services post-ship.
