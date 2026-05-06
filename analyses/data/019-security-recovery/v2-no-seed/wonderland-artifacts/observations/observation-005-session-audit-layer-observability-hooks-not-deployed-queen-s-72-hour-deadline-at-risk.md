## Observation 005: Session audit layer observability hooks not deployed; Queen's 72-hour deadline at risk

**Type:** post-deploy
**Severity:** sev2
**Time window:** 2026-05-05T14:52:00Z — ongoing

**Symptom:**

Rate-limit and lockout enforcement shipped and operational (error rate on /login endpoint 0%, requests correctly gated, lockout state machine returning expected 429/401 responses). Baseline telemetry confirms the mitigation is working. However: the Cat's minimal session-audit layer (ADR-002, shipping as part of unlock implementation) has no observability hooks. No metrics for session creation rate, token collision detection, session-revocation verification, or audit-trail write latency. The Queen's ruling requires 'session audit trails complete enough to answer what did this session access?' within 30 minutes. Audit logs cannot be read until they are instrumented. This blocks both the Hatter's scenario #2 verification and the Queen's evidence-gathering for GDPR notification.

**Affected scope:**

Session-audit layer in auth_service (all login paths, all data-access request validation, all session-revocation flows). No production visibility into whether sessions are being created, validated, or revoked correctly until instrumentation ships.

**Evidence:**
- Tweedledum's implementation (slug=incident-response-rate-limiting-and-lockout-enforcement) shows rate-limit and lockout operational; /login endpoint telemetry (error_rate, request_rate, lockout_state_transitions) all nominal.
- Cat's ADR-002 (slug=add-minimal-session-audit-layer-for-incident-response-visibility) proposes session_id generation and in-memory registry; no mention of observability hooks (metrics, logs, traces).
- Queen's ruling 003 (slug=investigate-successful-credential-stuffing-attempts-rule-on-gdpr-breach-notification-if-confirmed) depends on audit logs showing which sessions accessed data during attack window. Audit logs are generated but not observable without instrumentation.

**Probable domain:** backend

**Routed to:** tweedledum
