## Observation 008: Queen's breach-investigation deadline: audit parsing requires manual instrumentation

**Type:** anomaly
**Severity:** sev2
**Time window:** 2026-05-05T15:47:00Z — 2026-05-05T23:47:00Z

**Symptom:**

Queen ruling 002 requires forensic parse of audit logs to answer 'did any of the 4,127 attempted credentials succeed?' within 72 hours. Audit logs are shipping to /var/log/auth_audit.log in plaintext (session_id, endpoint, timestamp). No structured log sink (json, syslog aggregation, log query tool). The parse will require manual log review or ad-hoc grep. At 4,127 attempted credentials × N successful sessions, the manual surface is tractable but fragile — if logs rotate, get deleted, or become corrupted before forensic review, the investigation fails and Queen's breach-notification obligation becomes 'scope unknown.'

**Affected scope:**

audit trail for 4,127 credential attempts; Queen's GDPR Art. 33 breach-notification investigation; 72-hour window

**Evidence:**
- /var/log/auth_audit.log — plaintext, unstructured, no log aggregation sink configured
- logs: app=auth_service, event=session_created, window=14:23-15:47, count=(pending parse)

**Probable domain:** backend

**Routed to:** tweedledum
