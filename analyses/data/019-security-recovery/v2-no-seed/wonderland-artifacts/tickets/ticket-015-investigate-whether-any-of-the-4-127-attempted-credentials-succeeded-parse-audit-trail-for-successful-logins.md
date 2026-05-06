## Ticket 015: Investigate whether any of the 4,127 attempted credentials succeeded; parse audit trail for successful logins

**Sources:** ruling/investigate-whether-any-of-the-4127-attempted-credentials-succeeded-rule-on-gdpr-breach-notification-if-yes
**Owner:** dormouse
**Tier:** v1
**Estimate:** 1-1.5 hours, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: implement-rate-limiting-on-login-endpoint-per-queen-ruling
- Soft: —

**Description:**

Once the Tweedles ship the rate-limit implementation with audit logging, parse the audit_trail for the attack window (last 8 minutes, 203.0.113.42 source IP) and determine success rate. Specific: count (source_ip=203.0.113.42, auth_status=success) in audit_trail. If count > 0, the attack succeeded in compromising accounts. Report the count and the usernames of compromised accounts to the Queen immediately; she will rule on GDPR breach notification separately (ruling 002-investigate-whether-any-of-the-4127-attempted-credentials-succeeded). If count = 0, the rate-limit and lockout halted the attack before any credentials succeeded.

**Acceptance:**
- Audit trail is parsed for the attack window (203.0.113.42, last 8 minutes)
- Success-rate result is reported: (count of successful authentications, list of usernames if count > 0)
- Report is delivered to the Queen within 30 minutes of rate-limit implementation shipping

**Risk:**

If the audit trail is incomplete or malformed, the investigation is inconclusive. Mitigate by having the Tweedles include a validation check in the audit-log write path (log write fails loudly if the structure is wrong). If logs are incomplete, we document the gap as a finding for the post-incident review.
