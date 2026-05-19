## Ruling 003: Saved-state audit trail required for each note write to backend

**GUID:** 01KRXRTB6GG2E8KZ0W1RB4DCT3
**Severity:** high
**Domain:** logging-and-audit
**Source:** adr slug=server-authoritative-note-persistence-with-client-side-keystroke-buffer

**Citation:**

OWASP A09:2021 Logging and Monitoring Failures; standard practice for single-user transactional systems. Audit trails prove the system can account for state changes.

**Finding:**

If the backend persists note state without recording *when* and *by-what-user* each save occurred, the system cannot defend itself against claims of data loss, accidental overwrite, or tampering. Kohl's single-user assumption means the audit trail is simple (one actor), but it still must exist.

**Required Remediation:**

Each note write to the backend (create, update, delete, tag association/removal) must be logged with: timestamp (server time, not client time), actor (authenticated user identity), operation (create|update|delete|tag_add|tag_remove), note_id, and content hash (hash of the persisted state, not plaintext). Logs must be append-only and immutable for the duration of the project (they are single-user; retention can be short-term, but they cannot be modified retroactively).

**Acceptance Criteria:**
- Backend audit log table exists with schema: timestamp, actor_id, operation, note_id, content_hash
- Each save endpoint (POST /notes, PUT /notes/{id}, DELETE /notes/{id}, POST /notes/{id}/tags) writes to audit log before returning success
- Audit log entries are queryable (e.g., GET /audit?note_id={id} returns all operations on that note in order)
- Content hash is computed from the JSON-serialized note state, not from user input, so hash can be verified against the stored state

**Residual Risk:**

If the device is compromised (malware, physical theft post-unlock), the audit trail itself is accessible. This is accepted because the trail's purpose is to defend against accidental loss and system-level bugs, not against compromised-device attacks; those are mitigated by device-level security (OS lock, encryption at rest), not application-level logging.

**Compliance Implications:**

Audit trails are a standard requirement for transactional systems in most compliance frameworks (GDPR accountability principle, SOC 2 availability, HIPAA audit controls). Even for single-user MVP, establishing the pattern now prevents expensive retrofit later.

**Audit Reference:**

THREAT_GARDEN.md: Threat class 'Lost or overwritten notes due to missing audit trail' mitigated by this ruling.
