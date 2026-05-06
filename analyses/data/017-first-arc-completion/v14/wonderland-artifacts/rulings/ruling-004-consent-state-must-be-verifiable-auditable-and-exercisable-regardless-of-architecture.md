## Ruling 004: Consent state must be verifiable, auditable, and exercisable regardless of architecture

**Severity:** high
**Domain:** privacy
**Source:** proposal (hub-model ADR) + Cat's architectural concern + Alice's product tradeoff

**Citation:**

GDPR Articles 6 (lawful basis), 7 (conditions for consent), 12-22 (data subject rights), 32 (security of processing). Specifically: consent must be 'freely given, specific, informed and unambiguous' (Art. 4(11)); users must be able to withdraw consent (Art. 7(3)); the controller must demonstrate compliance (Art. 5(2) accountability principle).

**Finding:**

The three consent architectures (geo-scoped, unified, deferred) differ in *when* and *how* users encounter consent, but all three must satisfy the same GDPR requirements: consent must be recorded with specificity about what is consented to, the user must be able to access and withdraw it, and the system must have an auditable record proving these requirements were met. If the team chooses an architecture and implements it without explicit audit trails for consent state transitions (given, withdrawn, expired), the system will not be defensible under GDPR audits.

**Required Remediation:**

Before implementation begins, the team must specify: (1) what data the system will store to prove consent was collected (timestamp, user ID, consent version, jurisdiction detected, mechanism of collection); (2) how and where that consent record will be persisted and audit-logged; (3) how the user will be able to access, export, and withdraw their consent (this is a GDPR data subject right); (4) what happens to in-flight messages if consent is withdrawn mid-conversation (are they deleted? Archived? Anonymized?). The implementation must enforce these requirements at the code level, not as a post-facto audit artifact.

**Acceptance Criteria:**
- Consent state is persisted in a dedicated, audit-logged table/collection with timestamps and version tracking
- User can query their own consent history via a dedicated endpoint (GDPR right to access)
- User can withdraw consent via the same endpoint; withdrawal is timestamped and logged
- Message-send handler checks current consent state before accepting a message
- Audit logs show every consent state change (grant, withdrawal, expiry) with user ID, timestamp, and triggering action
- Compliance map confirms the consent audit trail is discoverable by a data protection audit

**Residual Risk:**

If a user withdraws consent mid-conversation, the system will no longer accept new messages from them, but existing messages remain in the database (per 'no message delete' scope constraint). This is a residual-rights tension: the user has exercised their right to withdraw consent, but their prior messages are not deleted. This is defensible under GDPR if documented as a residual risk and explained to the user at withdrawal time ('your prior messages will remain visible to your conversation partner; you cannot retroactively withdraw them'). Document this explicitly; do not assume the user understands it.

**Compliance Implications:**

GDPR Articles 6 (lawful basis must exist), 7 (consent must be freely given, specific, informed, unambiguous), 12-22 (data subject rights must be exercisable), 32 (security of processing requires audit trails). Failure to maintain an auditable consent record and to enable users to exercise withdrawal rights is a direct violation. The Rabbit should understand that this is a compliance requirement, not a feature request; it blocks shipment if absent.

**Audit Reference:**

Consent Architecture Decision (CAD-001): recording the choice of consent model, the audit trail specification, and the residual-rights decision regarding message retention post-withdrawal.
