## Ruling 011: Audit-trail revision identifier must use deterministic cryptographic hash of saved state

**GUID:** 01KRXXA1R8XKA7JH2MCC91FP1F
**Severity:** high
**Domain:** cryptography
**Source:** adr: audit-trail-schema-full-state-snapshots-with-timestamped-revisions

**Citation:**

CWE-330 Use of Insufficiently Random Values; OWASP A02:2021 Cryptographic Failures. The revision_id serves two functions: (1) collision detection for multi-tab scenarios (client-side), and (2) audit-trail versioning (server-side immutable record). If revision_id includes nondeterministic elements (timestamp, random nonce), the same saved state on two tabs will produce different IDs, breaking collision detection. If revision_id is predictable (sequential counter), it enables the localStorage-access attacker scenario the Queen flagged in prior ADR commentary. Deterministic cryptographic hash of the saved state is the only semantics that satisfy both constraints.

**Finding:**

The ADR names 'revision_id (opaque hash)' but does not specify whether the hash is deterministic (same state → same hash) or includes timestamp/nonce (different hashes for the same state at different times). Without this specification, the Tweedles will make different assumptions during contract negotiation, leading to either silent collision-detection failures (if timestamp-based) or predictability vulnerabilities (if sequential). The audit trail will record immutable snapshots correctly in both cases, but the application will not meet its architectural commitments.

**Required Remediation:**

The ADR must specify: revision_id = SHA256(canonical_json(saved_state)), where canonical_json ensures deterministic serialization (sorted keys, no whitespace variation). This ensures (a) same state always produces same hash (collision detection works), (b) hash is not predictable without knowing the content (security constraint satisfied), and (c) the audit log can reference revisions by deterministic ID. If timestamp-based versioning is needed (e.g., 'note was last edited at T1, T2, T3'), use separate timestamp fields in the audit log; do not embed timestamp into revision_id.

**Acceptance Criteria:**
- ADR revision-semantics section explicitly names the hash algorithm (SHA256, BLAKE3, etc.)
- ADR specifies that revision_id is deterministic: identical saved state produces identical revision_id regardless of when the save occurs
- ADR clarifies the relationship between revision_id (for collision detection) and state_hash (if it exists as a separate field; if they're the same field, say so explicitly)
- The Cat confirms the Tweedles will receive this specification before M3 contract negotiation begins

**Residual Risk:**

If the deterministic-hash semantics are not locked early, the Tweedles will ship revision_id implementations that diverge (one timestamp-based, one nondeterministic), and the collision-detection contract will be broken silently. This is not a production incident but a contract failure that cascades into multi-device sync problems downstream.

**Compliance Implications:**

The audit trail schema serves GDPR Art. 32 (security of processing) and SOC 2 CC6.1 (change management). Deterministic hashing ensures the audit trail is tamper-evident (any content change produces different revision_id, detecting manipulation). Timestamp-based or random-nonce revision_id would allow silent tampering (attacker changes content, generates new timestamp, audit log shows different revision_id but same canonical state).

**Audit Reference:**

Threat Garden entry: 'revision_id design for collision detection and tamper detection' — deterministic hash requirement confirmed. Security ruling on hash algorithm specificity enforced before Tweedle contract negotiation.
