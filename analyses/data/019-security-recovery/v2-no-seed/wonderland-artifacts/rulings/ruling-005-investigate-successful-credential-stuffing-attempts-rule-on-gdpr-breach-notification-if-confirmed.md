## Ruling 005: Investigate successful credential-stuffing attempts; rule on GDPR breach notification if confirmed

**Severity:** high
**Domain:** compliance
**Source:** credential-stuffing incident; Hatter scenario #2 surfaced the question

**Citation:**

GDPR Art. 33 (notification of a personal data breach to the supervisory authority); GDPR Art. 34 (communication of a personal data breach to the data subject). A 'breach' is unauthorized processing of personal data; successful authentication against a user account using a credential obtained from a previous breach constitutes reuse of personal data in violation of the user's authorization.

**Finding:**

4,127 login attempts in 8-minute window; current audit trail shows 0.2% success rate during attack window (8–9 successful attempts estimated). If any of those 8–9 successful attempts represent distinct user accounts, then personal data belonging to those users has been accessed by the attacker without authorization. GDPR Art. 33 requires notification to the supervisory authority (typically within 72 hours) if the breach results in a risk to the rights and freedoms of the data subject. Unauthorized account access = high risk. Notification timeline is non-negotiable; delaying this determination puts the team in violation of Art. 33 timing requirements.

**Required Remediation:**

Audit the login audit trail for successful authentication events during the 203.0.113.42 source-IP attack window (approximately 08:32–08:40 UTC). Parse success events for: (a) username of successful attempts, (b) user account ID, (c) timestamp, (d) whether successful login was followed by any data-access operations (API calls, queries, file reads) within the next 60 seconds. If any successful attempts exist, determine whether the accounts accessed are EU-resident (GDPR scope) or global (possible other jurisdiction scope). I will rule on notification scope and timeline once you confirm the success count and account scope.

**Acceptance Criteria:**
- Audit trail parsed and success-attempt list extracted (usernames, account IDs, timestamps, any follow-on data access)
- Geolocation of successful-attempt accounts confirmed (EU vs non-EU scope)
- Count of distinct accounts with successful unauthorized access confirmed
- If count > 0: Queen issues separate ruling on breach notification scope and timeline

**Residual Risk:**

If the audit trail is incomplete or timestamps are unreliable, we may undercount successful attempts. This is acceptable with documentation: if audit trail quality is questionable, we disclose the uncertainty in the GDPR notification and err toward over-notification (notify more users than may have been breached rather than fewer). The data owner is better served by false-positive notification than by false-negative silence.

**Compliance Implications:**

GDPR Art. 33 (supervisory authority notification) and Art. 34 (data subject communication). Non-compliance with Art. 33 timing results in potential regulatory fine (Art. 83, up to €10M or 2% annual revenue, whichever is higher). The investigation is the gate; notification ruling follows immediately after.

**Audit Reference:**

Incident-response thread, Queen ruling #2. Artifact: breach-investigation log with success-attempt audit trail, geolocation scope, and data-access confirmation. If breach confirmed, separate breach-notification ruling artifact will follow.
