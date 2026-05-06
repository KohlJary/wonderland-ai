## Ruling 001: GDPR Art. 17 erasure requires soft-delete with audit trail, not permanent deletion

**Severity:** critical
**Domain:** data-handling
**Source:** architectural proposal from Cheshire Cat; GDPR compliance scope

**Citation:**

GDPR Art. 17 (Right to Erasure); GDPR Art. 5(1)(e) (storage limitation); GDPR Art. 32 (security of processing)

**Finding:**

The directive states 'no delete,' which created ambiguity about whether users can exercise their GDPR Art. 17 erasure right. The Cat's proposal clarifies: soft-delete (deleted_at timestamp) is the correct model. Under GDPR, EU users have the right to request deletion of personal data. If we do not support erasure requests, the system violates GDPR Art. 17 and cannot be deployed in EU scope. Permanent deletion of messages is also incorrect because it destroys the audit trail that GDPR Art. 32 and Art. 33-34 (breach notification) require.

**Required Remediation:**

User(id, username, password_hash, created_at, deleted_at) and Message(id, conversation_id, sender_id, text_original, text_language, created_at, deleted_at). Soft-delete is mandatory on both tables. When a user requests erasure under Art. 17, the User.deleted_at timestamp is set, and all Message records where sender_id = deleted_user_id are also soft-deleted (or the message is anonymized). The system must log the erasure request (timestamp, requesting user, requester identity, justification) in a separate deletion_log table for audit purposes. Queries for message lists must filter out deleted_at IS NOT NULL.

**Acceptance Criteria:**
- User table has deleted_at column, nullable, indexed
- Message table has deleted_at column, nullable, indexed
- deletion_log table exists with (id, user_id, deleted_at, requested_by, request_reason, processed_at)
- API message list endpoints filter WHERE deleted_at IS NULL
- Erasure request handler sets User.deleted_at and cascades to Message records; logs to deletion_log
- Caterpillar review confirms queries do not expose deleted data

**Residual Risk:**

Soft-delete does not erase data from backups immediately; recovery of deleted data from backup is technically possible. This is acceptable under GDPR if the system has a documented backup and disaster-recovery policy that specifies retention windows and deletion procedures. Document the backup retention policy in the Compliance Map (Queen artifact).

**Compliance Implications:**

GDPR Art. 17 (Right to Erasure); GDPR Art. 5(1)(e) (storage limitation); GDPR Art. 32 (security of processing). Absence of this ruling means the system cannot be deployed in EU scope.

**Audit Reference:**

Threat Garden entry: 'GDPR erasure request handling'; Compliance Map entry: 'GDPR Art. 17 — deletion procedure.'
