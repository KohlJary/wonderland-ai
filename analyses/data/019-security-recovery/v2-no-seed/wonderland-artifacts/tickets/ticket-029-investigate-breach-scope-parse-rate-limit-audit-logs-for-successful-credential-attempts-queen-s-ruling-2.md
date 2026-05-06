## Ticket 029: Investigate breach scope: parse rate-limit audit logs for successful credential attempts (Queen's ruling 2)

**Sources:** ruling-002, ticket-rabbit-investigate-breach-scope
**Owner:** Dormouse
**Tier:** v1
**Estimate:** 1 to 2 hours, 70% confident
**Status:** open

**Dependencies:**
- Blocks: queen-secondary-ruling-on-gdpr-notification
- Blocked by: ticket-tweedledum-implement-rate-limiting-on-login-endpoint-per-queen-ruling
- Soft: —

**Description:**

Once the rate-limit implementation ships and logs are flowing, parse the attack window (last 8 minutes before rate-limit deployment) for evidence of successful credential attempts. Query: for each of the 4,127 login attempts across 2,803 distinct usernames, did any return 200 (success) instead of 401 (failure)? Output a count of successful attempts, a list of affected user accounts (if any), and a timeline of when the successes occurred. This is the Queen's evidence for determining whether a GDPR Art. 33 breach-notification obligation exists. If success count is 0, the attack was caught before any data exposure; Queen rules accordingly. If success count is >0, Queen makes secondary ruling on notification scope, user communication, and credential-reset requirements. Keep this investigation isolated from production queries; use audit logs only, do not query live user data. Time sensitivity: complete within 60 minutes of rate-limit deployment so Queen can rule on notifications by end-of-business.

**Acceptance:**
- Audit logs parsed for successful login attempts during attack window (8-minute window before rate-limit deployment)
- Count of successful attempts documented (zero or >zero)
- If >zero: list of affected user accounts, timestamps of successful attempts, IP addresses of successful requests
- Dormouse publishes findings to Queen with confidence level (certain, probable, uncertain based on log completeness)
- Queen can make notification ruling based on findings

**Risk:**

If audit logs are incomplete or corrupted during attack, success count may be uncertain. If so, Queen must rule on notification based on 'success probable but unconfirmed' posture. Residual risk documented and accepted per Queen's ruling on incomplete visibility.
