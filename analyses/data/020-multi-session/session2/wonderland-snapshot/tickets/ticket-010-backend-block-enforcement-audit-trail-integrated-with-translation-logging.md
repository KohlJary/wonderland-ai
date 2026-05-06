## Ticket 010: Backend: Block enforcement audit trail integrated with translation logging

**Sources:** story: system-operator-verifies-block-enforcement-without-data-leakage
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: ticket: backend-logging-and-audit-trail-for-translation-events
- Blocked by: ticket: backend-block-and-unblock-endpoints-and-blocking-history-audit
- Soft: ticket: backend-get-conversations-id-messages-api-with-translation-status

**Description:**

Extend the existing logging/audit infrastructure (ticket-6) to capture block events: block initiated, unblock initiated, message visibility check executed + blocked messages filtered. No new storage; uses the same audit table as translation events. Sam queries a single audit log and sees complete picture: message lifecycle (translation status), delivery status, block events, all timestamped.

**Acceptance:**
- Audit log includes block/unblock events with (conversation_id, actor_id, target_id, event_type, timestamp)
- Audit log includes message-visibility-check events showing which messages were filtered due to blocks
- Sam can query audit log by conversation_id and see full chain of translation + block events
- No blocked message content leaks in audit logs (only block fact is recorded, not message text)

**Risk:**

Low. This extends existing logging infrastructure. The risk is if the logging ticket (ticket-6) hasn't shipped yet—in that case, this blocks on that ticket.
