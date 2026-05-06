## Observation 002: Critical observability gap: no production instrumentation for rate-limit decisions or lockout events

**Type:** incident
**Severity:** sev1
**Time window:** 2026-05-05T14:15:00Z — ongoing

**Symptom:**

Current incident diagnosis required manual log inspection and account status queries. No metrics exist for: rate-limit threshold crosses per IP, rate-limit threshold crosses per email, lockout event rate, lockout reason distribution, legitimate false-positive rate (legitimate users on shared IPs during attack). Hatter's test_scenario 'Monitoring gap — rate-limit and lockout events should be observable in production' identified this gap pre-incident; gap was not remedied before attack surface was activated. Diagnosis speed was degraded by absence of: dashboard for rate-limit event velocity, alert for account lockout spike, trace correlation between failed login attempt and lockout decision.

**Affected scope:**

Auth service instrumentation. Affects incident response speed, attack pattern visibility, false-positive detection.

**Evidence:**
- Hatter's test_scenario artifact (slug: monitoring-gap-rate-limit-and-lockout-events-should-be-observable-in-production) — filed pre-incident, severity=high, concern=observability_prerequisite
- Grep of auth service codebase (last commit 2026-04-28): no histogram for 'auth.rate_limit.decisions', no counter for 'auth.account.lockout_events', no tags for reason/attack_pattern
- Incident timeline: Alert fired 14:18 UTC (3min lag from attack start); manual inspection required until 14:31 UTC for full pattern visibility. Automated detection would have reduced lag to <30sec.

**Probable domain:** backend

**Routed to:** tweedledum
