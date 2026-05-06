## Observation 013: Session-audit observability hooks incomplete; Dormouse cannot verify session behavior in production

**Type:** anomaly
**Severity:** sev2
**Time window:** 2026-05-05T14:47:00Z — 2026-05-05T15:47:00Z

**Symptom:**

Session audit layer deployed (confirmed); audit logs recording (session_id, endpoint, timestamp). But observability hooks — the Dormouse's windows into how sessions are being created, validated, and revoked — are not instrumented. The Dormouse cannot currently: (1) verify that session tokens are being issued correctly, (2) detect whether session creation is failing under load, (3) confirm that session revocation on unlock is working, (4) answer 'what did session X access?' with sufficient granularity for the Queen's breach investigation. The Cat's minimal session-audit design is sound; the implementation is incomplete on the observability side.

**Affected scope:**

Dormouse's ability to respond to production incidents involving session behavior; Queen's ability to complete 72-hour breach investigation with session-access granularity; Tweedles' ability to test unlock-flow correctness via telemetry.

**Evidence:**
- Dormouse observation (turn 12): 'Session audit layer deployed; observability instrumentation incomplete'
- Dormouse concern (turn 17): 'Dormouse telemetry gap: session-creation telemetry, session-access audit shape, session revocation verification not yet specified'
- Rabbit's blocking ticket (turn 20): 'Specify session-telemetry observability hooks required for production incident response'
- No Dormouse observation of session-layer telemetry in any turn; no session metric baseline established

**Probable domain:** observability + backend implementation

**Routed to:** dormouse
