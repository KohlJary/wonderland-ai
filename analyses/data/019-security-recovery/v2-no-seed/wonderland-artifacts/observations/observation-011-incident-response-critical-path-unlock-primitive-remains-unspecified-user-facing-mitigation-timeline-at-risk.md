## Observation 011: Incident-response critical path: unlock primitive remains unspecified; user-facing mitigation timeline at risk

**Type:** incident
**Severity:** sev2
**Time window:** 2026-05-05T14:23:00Z — ongoing

**Symptom:**

Rate-limit enforcement is operational and halting the attack (telemetry: attack traffic rejected, legitimate login attempts being rate-limited at expected thresholds). Session audit layer deployed. But the unlock primitive—the mechanism by which locked-out legitimate users regain access—remains unspecified in code. The Queen has ruled on three unlock requirements (clear error messaging, 5-minute unlock window, attacker-proof authorization). The Rabbit has decomposed implementation tickets. But no Tweedles implementation artifact exists yet for the unlock endpoint or recovery-primitive integration. The unlock tickets are soft-blocked waiting for architectural confirmation. Timeline: Queen's ruling landed this turn; 60-minute window for user-facing mitigation begins now.

**Affected scope:**

Locked-out users (n=47 known, likely +8-12 collateral on shared IPs). Error UX for rate-limited login attempts. Unlock authorization flow (email/SMS/security-question—primitive still not selected). Timeline risk: if unlock does not ship within 60 minutes, locked-out users remain locked until the 5-minute automatic-lockout TTL expires (next unlock-via-waiting window: 14:28-14:33 UTC, approximately 5-10 minutes from now). If 10+ users exhaust patience and contact support before self-service unlock is available, secondary incident: support queue overload during active incident response.

**Evidence:**
- Rate-limit telemetry: 203.0.113.42 rejected at 14:23 UTC, continues rejecting incoming attempts at expected thresholds through present
- Tweedledum implementation artifact (turn 8): rate_limit_middleware.py shipped; unlock endpoint missing
- Rabbit ticket decomposition (turn 14): 'implement account-recovery primitive' and 'implement account unlock workflow' both marked soft-blocked pending architectural confirmation
- Queen's rulings (this turn, slugs=locked-out-users-must-receive-clear-actionable-error-messaging-immediately, account-unlock-must-be-available-to-legitimate-account-owners-within-5-minutes-of-attempting-unlock, unlock-must-not-be-possible-for-attackers-with-the-breached-password): three sequential requirements with no conditional logic—all three must be true
- Cat's ADR-001 (turn 9): unlock authorization boundary named; implementation specification absent
- Current time: 14:27 UTC (4 minutes since rate-limit shipped); 5-minute automatic-lockout TTL expires at 14:28 UTC; 60-minute user-facing mitigation window closes at 15:23 UTC

**Probable domain:** backend (recovery primitive implementation) + frontend (error UX, unlock workflow UX)

**Routed to:** white_rabbit
