# ADR-001: Rate-limit messages by client IP with runtime observability and spoofing defense

## Context

The /api/messages endpoint needs protection against burst abuse. Three constituencies have distinct needs: developers integrating the API must understand rate limits (clear 429 response + Retry-After header); operators in production must see rate-limit events and tune the threshold at runtime; the deployment team must know whether client identification is safe against header spoofing. A single-instance, application-layer rate limiter cannot serve all three: it provides no cross-instance coordination (leaving multi-instance deployments vulnerable to distributed abuse) and no production-grade observability (operators cannot see or adjust behavior without redeploy). The architecture must assume distributed deployment and make the rate limiter a first-class production component.

## Decision

Implement a distributed rate limiter that: (1) identifies clients by X-Forwarded-For header when present, falling back to remote address; (2) emits observable events for each rejection (client ID, timestamp, current bucket state); (3) allows runtime threshold tuning via configuration system (no redeploy); (4) documents the trust model clearly so operators understand when X-Forwarded-For is valid in their deployment; (5) provides a configuration flag to disable X-Forwarded-For and use only remote address for deployments that cannot trust proxy headers.

## Tradeoffs

- Distributed coordination adds latency and complexity — each request must consult shared state (Redis, DynamoDB, or equivalent). This is acceptable because the alternative is a false rate limit that fails under multi-instance load. The latency cost is small relative to message send latency.
- X-Forwarded-For is trusted by default, which is safe only if the load balancer is the *only* entity able to set it. Deployments that receive requests from untrusted proxies must explicitly configure header validation or disable X-Forwarded-For entirely. Documentation must make this explicit.
- Runtime tuning requires the rate limit value to live in a queryable configuration system (not baked into the binary). This costs a small architectural dependency. The alternative is operator-hostile: tweaking limits requires code change and redeploy.
- The 10 requests/minute threshold is provisional and data-driven — this ADR does not prescribe the number. Story 002 flags that if the limit is too strict, operators will disable it. Once shipped, metrics from story 002's acceptance criteria will show whether this threshold is right for real traffic patterns. If wrong, it is tunable without this ADR being revisited.
- Open: the storage backend for distributed rate-limit state is not yet specified. Redis is simplest; DynamoDB is acceptable if you want to reduce operational complexity. This choice should be driven by existing infrastructure and consistency requirements. The architecture is storage-agnostic; the contract is: atomic compare-and-set on a per-IP bucket, with visibility into bucket state for debugging.

## Status

Proposed
