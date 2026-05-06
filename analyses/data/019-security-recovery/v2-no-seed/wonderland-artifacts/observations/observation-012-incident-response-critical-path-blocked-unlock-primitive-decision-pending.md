## Observation 012: Incident-response critical path blocked; unlock primitive decision pending

**Type:** incident
**Severity:** sev1
**Time window:** 2026-05-05T14:23:00Z — 2026-05-05T15:47:00Z

**Symptom:**

Rate-limit and lockout enforcement operational (confirmed turn 8, live). Session audit layer deployed (turn 12). But unlock path — the mechanism by which 47 locked-out users regain access — remains unimplemented. The Rabbit's blocking ticket (slug=resolve-account-recovery-primitive-availability-and-threat-model-requirements) identifies the architectural gate: which account-recovery primitive (email token, SMS OTP, security question) does the Queen authorize? Without that ruling, the Tweedles cannot finalize the unlock UX contract. Production data: rate-limit is holding; new attack attempts from source IP are rejected. User-facing data: zero unlock endpoints operational; 47 accounts remain locked; self-service recovery unavailable.

**Affected scope:**

All 47 locked-out users; any additional user attempting login from attacked IP ranges during the next 90 minutes until automatic lockout TTL expires. Frontend unlock UX; backend recovery primitive; customer-facing incident timeline.

**Evidence:**
- Rate-limit enforcement confirmed in Tweedledum's implementation artifact (turn 8): 'IP 203.0.113.42 rate-limited after 10 attempts/minute'
- Session audit layer deployed (Dormouse observation, turn 12): 'Session audit layer deployed; observability hooks incomplete'
- Tweedledum implementation artifact (turn 8) contains no unlock endpoint; no recovery primitive calls
- Caterpillar review not yet available; cannot confirm unlock UX contract completeness
- Rabbit's blocking ticket (turn 21) names the gate: 'Resolve account-recovery primitive availability and threat-model requirements'
- Mad Hatter test scenarios (turn 19) marked as 'awaiting architectural clarity' on which primitive is in-scope

**Probable domain:** architecture + implementation (hybrid decision)

**Routed to:** cheshire_cat
