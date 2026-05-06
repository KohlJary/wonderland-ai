## Ruling 014: Session-audit log format specified for breach investigation and observability

**Severity:** critical
**Domain:** logging-and-audit
**Source:** Dormouse's observability-gaps concern (turn 14); Queen's breach-investigation requirement (ruling-002)

**Citation:**

GDPR Art. 33 — breach notification requires demonstrable evidence of what data was accessed. Session-audit logs are the evidence. Log format must be auditable without logging sensitive data.

**Finding:**

The minimal session-layer architecture is sound, but audit-log format is unspecified. The Queen cannot investigate breach scope without knowing what fields the logs contain. The Dormouse cannot parse logs without format specification. Unspecified logging = invisible session layer.

**Required Remediation:**

Specify and implement session-audit logs with format: (session_id, user_id, endpoint_accessed, timestamp, response_status_code, data_sensitivity_flag). The data_sensitivity_flag indicates whether the endpoint accessed high-sensitivity data (PII, credentials, payment info) or low-sensitivity data (public profile, metadata). Logs are written to disk before response is sent to client (durability-first). Logs are retained for 90 days post-incident.

**Acceptance Criteria:**
- Session-audit logs are written to persistent storage before HTTP response is sent
- Log format is (session_id, user_id, endpoint, timestamp, status, sensitivity_flag)
- Dormouse's telemetry pipeline can parse logs within 60 seconds of write
- A 6-hour sample of logs is available for Queen's breach investigation by end of business today
- Queen can answer 'did this session access sensitive data?' by reading the audit logs
- Logs are encrypted at rest and access-controlled to security + SRE team only

**Residual Risk:**

Session-audit logs themselves are sensitive (they reveal which sessions accessed which endpoints). This is mitigated by: (1) separate storage from application data, (2) encryption at rest, (3) access control restricted to security team. Residual risk of log-breach leaking session patterns is acceptable and documented.

**Compliance Implications:**

GDPR Art. 33 (72-hour breach notification) — audit logs are the evidence that fulfills this requirement. Without logs, the team cannot demonstrate what data was exposed, which makes timely notification impossible.

**Audit Reference:**

Ruling-014: Session-audit log format specified; implementation of audit hooks must complete before session-layer merges to production.
