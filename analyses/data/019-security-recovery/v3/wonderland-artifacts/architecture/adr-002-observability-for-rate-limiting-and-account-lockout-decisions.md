# ADR-002: Observability for rate-limiting and account-lockout decisions

## Context

The rate-limiting and account-lockout controls mitigate credential-stuffing attacks by blocking IPs after N failures and locking accounts after M failures. Both controls are implemented and tested. However, the decisions these controls make are not observable in production. When a rate-limit check fires, no event or metric is emitted. When an account is locked, no signal reaches the observability layer. The Queen has ruled that observability is v1-blocking (rulings 001-003), specifically to enable breach-notification determination (which accounts succeeded during the attack, and thus whose passwords were compromised) and post-incident forensics (which IPs were rate-limited, which accounts were locked, what was the attack surface). The Caterpillar's review confirmed that the current implementation produces no such signals. This is not a testing gap or a logging gap — it is an architectural gap: the system's enforcement mechanism has no observable boundary.

## Decision

The rate-limiter and account-lockout implementations must emit or expose observable events that allow external systems (observability layer, breach-notification job, incident-response tooling) to see: (1) when a rate-limit decision is made (source_ip, failure_count, threshold, window_expires_at), (2) when an account lockout decision is made (email, failure_count, threshold, lockout_duration), (3) when an account is unlocked or rate-limit is cleared (email, source_ip, unlock_method), (4) when a successful login occurs (email, source_ip, occurred_at). These events should be queryable with cardinality bounds (e.g., per IP, per email) to support both real-time dashboards and post-incident forensics. The implementation approach (metrics hooks, event log, audit table columns) is the Tweedles' choice; the contract is the architecture.

## Tradeoffs

- Adding observable signals increases latency on the login path (each rate-limit/lockout decision must record/emit an event). Mitigation: async event emission or metrics batching, or accept millisecond-scale latency for synchronous audit-table writes.
- Observability cardinality can explode during a sustained attack (millions of rate-limit decisions from thousands of IPs). Mitigation: aggregate metrics with bounded cardinality (top-10-ips-by-request-count), or implement cardinality limits in the observability layer.
- Event emission during an active attack could itself become a target (emit-based DoS). Mitigation: keep event emission logic simple and separate from the policy logic; use async emission so policy decisions are not slowed by observability infrastructure.
- Breach-notification requires correlating rate-limit/lockout decisions with successful-login events, and both with the attack timestamp. This requires incident state (attack_start, attack_end) to be explicitly recorded somewhere. Mitigation: incident-response tooling must capture these boundaries; observability layer must support time-window queries.
- If observability is deferred post-incident, the current implementation has no way to replay it from first-principles (FailedAttempt table does not distinguish rate-limit events from password-failure events; Session table does not mark logins during attack window). Mitigation: extend FailedAttempt.reason enum to include 'rate_limited' and 'account_locked'; mark Session rows with an 'occurred_during_incident' flag so breach-notification queries can find them.
- The password-reset endpoint (not yet implemented) will need separate rate-limiting policy to avoid locking users out of password recovery. Observability contract must account for this separately (password-reset-initiated, password-reset-succeeded) to avoid false positives in breach-notification.
- Production durability of observability: in-memory metrics are lost on restart; audit tables can have write lag. Mitigation: observability contract should specify synchronous vs. async requirements (breach-notification queries run against durable audit trail; incident dashboard can read in-memory metrics).

## Status

Proposed
