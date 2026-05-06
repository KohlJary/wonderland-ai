## Observation 012: Breach-notification ruling depends on observability instrumentation; both rulings are v1-blocking but sequenced incorrectly

**Type:** incident
**Severity:** sev1
**Time window:** 2026-05-05T14:00:00Z — ongoing

**Symptom:**

The Queen issued two interdependent rulings for the credential-stuffing incident: #2 requires breach-notification for accounts where credentials succeeded; #3 requires observability of rate-limit and lockout events before v1 ship. The current implementation satisfies neither ruling completely. Observability for rate-limit/lockout decisions (rejection events) is absent; observability for *successful authentications during the attack window* is entirely absent. Without successful-login events visible in production telemetry, the breach-notification obligation (#2) cannot be discharged—we will not know which users to notify about compromised credentials. The two rulings are load-bearing on each other: #3 (observability) is a prerequisite for #2 (breach notification). Shipping v1 with #3 incomplete means shipping v1 with #2 unexecutable.

**Affected scope:**

Breach-notification work (compliance); user notification for compromised accounts during attack window (2026-05-05T14:23—14:47 UTC, ~47 compromised accounts); observability contract for rate-limiting and lockout events; implementation scope for successful-login event instrumentation.

**Evidence:**
- Queen's ruling #2 (breach-notification obligations): requires determination of which accounts had successful logins during attack period
- Queen's ruling #3 (observability required before v1 ship): requires production telemetry for rate-limit and lockout events
- Current implementation (Tweedledum): rate-limiting and lockout logic deployed; no instrumentation for successful-login events; no observable signal when rate-limit decisions fire
- Caterpillar review: flagged missing observability; did not explicitly gate on the connection between breach-notification obligation and observability prerequisite
- Alice's concern: the two rulings form a dependency chain that the implementation plan does not reflect

**Probable domain:** implementation, observability, compliance

**Routed to:** caterpillar
