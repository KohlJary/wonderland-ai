## Ticket 008: Implement breach-notification determination (which accounts succeeded in attack) per Queen's ruling

**Sources:** ruling: breach-notification-obligations-credential-stuffing-success-determination-and-user-notification
**Owner:** Dormouse
**Tier:** v1
**Estimate:** 1-2 hours, 75% confident
**Status:** open

**Dependencies:**
- Blocks: ticket: implement-user-notification-for-breached-accounts
- Blocked by: ticket: implement-rate-limit-and-lockout-observability-for-breach-notification-determination
- Soft: —

**Description:**

Dormouse: query production telemetry to determine which user accounts experienced successful login during the credential-stuffing attack window (Dormouse's observation: 8-minute window starting ~[timestamp from observation]). Use rate-limit and lockout observability (previous ticket) to cross-reference: emails that saw high failed-attempt counts AND also saw successful logins during the window = accounts where credentials were compromised. Produce a list of affected emails and successful-login timestamps for breach-notification work.

**Acceptance:**
- List of affected email addresses (accounts with successful logins during attack window)
- Successful-login timestamps and source IPs for audit trail
- Confidence level on breach determination (e.g., 'high confidence: 14 logins from attacker IP; low confidence: 2 logins from same IP as >100 failed attempts')
- Data ready for notification flow (next ticket)

**Risk:**

Attack window timing may be uncertain if Dormouse's observation doesn't pin exact start time. Use the 'anomaly detected' timestamp as window start and assume attack began minutes before detection. Queen should clarify the window definition.
