## Ticket 006: Backend: Logging and audit trail for translation events

**Sources:** story-003, adr-message-visibility-and-audit-contract-dual-language-display-status-persistence-polling-based-sync
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket-002
- Soft: —

**Description:**

Every translation event (pending → translated, pending → failed, retries) is logged with timestamp, message_id, source_language, target_language, success/failure, error_code (if failed), and (for Sam's observability) operator-queryable. Create a TranslationEvent log table or structured log output. Ensure logs are queryable by message_id and timestamp for audit and debugging. No change to Message schema or API response — logging is purely backend observability.

**Acceptance:**
- Every translation service call is logged
- Log includes timestamp, message_id, language_pair, success/failure, error_code
- Logs are queryable by message_id (for single-message audit)
- Logs are queryable by timestamp (for batch debugging)
- Translation failures are queryable separately for SRE response

**Risk:**

If logging volume is high, storage could bloat. Plan for log rotation and archival in post-launch ticket.
