## Observation 004: Queen's rulings require observability instrumentation not yet present in implementation plan

**Type:** anomaly
**Severity:** sev2
**Time window:** 2026-05-05T14:45:00Z — ongoing

**Symptom:**

Queen's ruling on breach-notification-obligations requires distinguishing 'confirmed compromised accounts' from 'attacked but not compromised accounts'. Implementation plan (Tweedles' tickets) does not include instrumentation to track this distinction in production. Rate-limiting events are logged; secondary-activity detection (the trigger for 'confirmed compromise') is not instrumented. Without production observability of secondary-activity patterns, breach-notification decision will be made on logs after-the-fact rather than detected in real time, delaying user notification.

**Affected scope:**

Breach notification compliance; user notification latency; real-time detection of account compromise.

**Evidence:**
- ruling artifact: ruling slug=breach-notification-obligations-credential-stuffing-success-determination-and-user-notification — requires 'determination of which accounts were successfully compromised' and 'user notification within [SLA]'
- implementation tickets: slug=implement-rate-limiting-and-account-lockout-hardening-to-stop-credential-stuffing-attack — specifies rate-limit and lockout events, does not specify secondary-activity-detection instrumentation
- current production logs: no structured secondary-activity event type; detection would require manual log parsing or Tweedles to write ad-hoc post-incident analysis

**Probable domain:** backend

**Routed to:** tweedledum
