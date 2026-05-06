# ADR-001: Auth defense-in-depth: IP rate limiting + per-email account lockout

## Context

Credential-stuffing attack (SIG-incident-response) exploited the absence of rate limiting and lockout. The attack shows two patterns: bulk enumeration from a single IP (4,127 attempts from 203.0.113.42), and potential distributed attack across IPs on specific target emails. The mitigation must defend against both without creating false positives or escape hatches.

The team has implemented IP-based rate limiting (sliding window, 10 requests/minute) and per-email account lockout (5 failures → lock until manual reset or configurable duration). The architectural question: does this composition correctly prioritize threats and handle the seams?

## Decision

Defense-in-depth: IP-based rate limiting (10 requests/minute per source IP, 1-minute sliding window) catches bulk enumeration attacks from single sources. Per-email account lockout (5 failed attempts, configurable duration, default: permanent until manual reset during incident, 15 minutes in production) catches both targeted attacks and distributed credential-stuffing (since any email that absorbs 5 failures from any IP mix will lock). Both controls feed the same FailedAttempt audit table for forensic visibility. Rate limiter and lockout state are in-memory with TTL expiry for incident response speed; migrate to Redis for production durability. HTTP responses map rate-limit and lockout failures to 429 (too many requests), credential failures to 401 (authentication failed), preserving the user-facing ambiguity needed to avoid email enumeration attacks.

## Tradeoffs

- Per-IP rate limiting is not a complete defense against distributed attack; it is a friction multiplier. The complete defense against distributed credential-stuffing is the per-email lockout. If this tradeoff is unacceptable (attacker can still hit a target 5 times across 10 IPs), the mitigation is to lower the failure threshold to 3 or implement distributed-lockout coordination (requires shared state; deferred to production hardening).
- False positives on shared networks: users sharing a corporate firewall or home ISP block can trigger the per-IP rate limit legitimately. This is acceptable for login (users can retry after 1 minute) but becomes critical at password-reset flows where the user is *already* locked and needs to self-recover. Password-reset email-address lookup must bypass the rate limiter; this seam is identified but not yet implemented.
- In-memory rate-limit and lockout state does not persist across service restarts. During an active incident, if the service restarts, the rate-limit cache clears and an attacker can resume bulk enumeration from a known IP. This is acceptable for SIGv1 (incident response is a short-lived state; the IP is likely to be filtered at the network layer or incident-response deploys a patch). For production, migrate both controls to Redis or a shared cache.
- Lockout duration choice: defaulting to permanent (until manual reset) during incident response maximizes impact on the attacker; requiring manual admin unlock is a recovery friction that's acceptable when an on-call is engaged. Configurable duration (e.g., 15 minutes) for production mode trades off incident-response speed for automatic recovery. The code supports both; the choice is a deployment configuration.
- The per-email lockout resets on successful login (via record_success), allowing legitimate users to recover by successfully entering their password. This assumes users know their own credentials even if they're temporarily locked; if users don't know credentials, password-reset becomes their recovery path, which requires the rate-limit bypass mentioned above.

## Status

Proposed
