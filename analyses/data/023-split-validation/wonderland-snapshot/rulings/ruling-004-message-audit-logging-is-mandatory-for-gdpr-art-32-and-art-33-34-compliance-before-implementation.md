## Ruling 004: Message audit logging is mandatory for GDPR Art. 32 and Art. 33-34 compliance before implementation

**Severity:** high
**Domain:** logging-and-audit
**Source:** GDPR Art. 32 (security of processing), Art. 33-34 (breach notification), Art. 28 (processor obligations)

**Citation:**

GDPR Art. 32 (security of processing); GDPR Art. 33-34 (breach notification); ISO/IEC 27001 (Information Security Management); OWASP A09:2021 (Logging and Monitoring Failures)

**Finding:**

The Cat's architectural proposal does not specify audit logging, but GDPR Art. 32 requires technical measures to ensure the security of personal data. For a message system handling EU user data, this includes audit trails of: (1) message creation (who, when, language); (2) message read/access (who accessed, when); (3) translation service calls (which service, when, data volume); (4) deletion/erasure requests (who requested, when, processed when); (5) access to deleted data (if attempted); (6) system errors during message processing. These logs are also required to fulfill GDPR Art. 33-34 (breach notification) — if a breach occurs, the system must be able to determine what data was accessed and when. Without audit logging, the system cannot demonstrate compliance or conduct a proper breach investigation.

**Required Remediation:**

Implement audit logging for all message-handling operations before the Tweedles ship any implementation to production. The audit log must include: (timestamp, user_id, action, resource_id, status, error_if_any). Actions to log: MESSAGE_CREATED, MESSAGE_READ, MESSAGE_TRANSLATED, USER_DELETED, TRANSLATION_SERVICE_CALLED, DELETION_LOG_ENTRY. Logs must be immutable (append-only) or stored in a separate audit database. Logs must be retained for at least 12 months (or per regulatory requirement for the jurisdiction). Logs must not include the message text itself (to avoid logging personal data twice); they may include message_id and data volume (character count).

**Acceptance Criteria:**
- Audit log table or database created: (id, timestamp, user_id, action, resource_id, resource_type, status, error_message)
- All message operations log to audit table before commit
- Translation service calls are logged: (timestamp, message_id, service_name, source_lang, target_lang, character_count, response_time, status)
- Deletion operations are logged: (timestamp, deleted_user_id, requester_id, request_reason, processed_at)
- Audit logs are immutable (no updates, only appends) or stored in separate audit DB
- Audit log retention policy is documented (minimum 12 months)
- Caterpillar review confirms all message paths hit audit logging

**Residual Risk:**

Audit logs themselves become a data-handling surface; they must be protected from unauthorized access. Ensure audit logs are not exposed in error messages, debug output, or user-accessible endpoints. This is addressed in the subsequent ruling on logging-and-audit boundaries.

**Compliance Implications:**

GDPR Art. 32 (security of processing); GDPR Art. 33-34 (breach notification and investigation); GDPR Art. 5(1)(a) (lawfulness, fairness, transparency — audit trails support this).

**Audit Reference:**

Compliance Map entry: 'GDPR Art. 32 audit logging'; Threat Garden entry: 'message system audit trail.'
