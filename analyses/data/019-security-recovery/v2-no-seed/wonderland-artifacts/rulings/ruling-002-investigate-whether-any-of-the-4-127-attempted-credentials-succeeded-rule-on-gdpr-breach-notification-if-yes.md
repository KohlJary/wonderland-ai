## Ruling 002: Investigate whether any of the 4,127 attempted credentials succeeded; rule on GDPR breach notification if yes

**Severity:** critical
**Domain:** compliance
**Source:** observation from Dormouse: 4,127 attempts reported, success rate 0.2%, implies ~8 successful logins possible

**Citation:**

GDPR Art. 33 (notification of a personal data breach to the supervisory authority without undue delay and in any case not later than 72 hours), Art. 34 (communication of a personal data breach to the data subject without undue delay). CWE-522 Insufficiently Protected Credentials.

**Finding:**

The Dormouse reports success rate dropped to 0.2% during the attack window. This is consistent with the attacker's credential list containing ~8 valid credentials (0.2% of 4,127 ≈ 8). If any credentials succeeded, account access was granted to the attacker. This constitutes a confirmed personal data breach (unauthorized access to user accounts = unauthorized processing of personal data per GDPR definitions). Failure to notify within 72 hours is a compliance violation with regulatory and financial penalties.

**Required Remediation:**

Immediately (within 30 minutes): (1) Query audit logs for successful /login attempts from source IP 203.0.113.42 during the attack window (last 8 minutes per Dormouse report). (2) For each successful login, identify the username, timestamp, and any data accessed by that session (use session telemetry). (3) Count total successful breached accounts. (4) If count > 0: document finding, identify affected users, assess harm (what data did the breached sessions access?), and notify Data Protection Officer and Legal immediately with the count and scope. (5) Prepare breach notification payload for GDPR Art. 33 (supervisory authority) and Art. 34 (affected data subjects) with details on: when breach occurred, what data was accessed, what we are doing to mitigate, what users should do. Notification must be filed within 72 hours of breach confirmation.

**Acceptance Criteria:**
- Audit-log query completed within 30 minutes; successful login count from 203.0.113.42 determined
- If count = 0: document 'no successful breaches confirmed' and close this ruling as residual risk accepted (attack was rate-limited before any succeeds)
- If count > 0: affected user list generated, DPO and Legal notified within 45 minutes of this ruling with full breach scope
- Breach notification prepared (Art. 33 to supervisory authority, Art. 34 to affected users) and queued for filing within 72 hours of breach discovery

**Residual Risk:**

If the query returns successful logins but the audit trail does not capture which data was accessed during those sessions, harm assessment becomes incomplete. This is acceptable short-term (file the breach notification with 'scope unknown pending audit trail reconstruction') but must be resolved within 24 hours. This reveals a logging gap: session audit trails must be complete enough to answer 'what did this session access?' for any future breach investigation.

**Compliance Implications:**

GDPR Art. 33(1): breach notification to supervisory authority required within 72 hours if there is no reason to believe no risk to the rights and freedoms of natural persons. Unauthorized account access almost always poses such a risk (account compromise, identity theft, data exfiltration). Art. 34: notification to affected data subjects required unless breach did not create significant risk. High bar; most breaches require notification. This is not optional compliance — it is a hard statutory deadline with significant penalties for non-compliance (fines up to €20M or 4% of global annual turnover, whichever is higher).

**Audit Reference:**

incident-response thread, breach-investigation ruling, filed with timestamp and DPO/Legal escalation
