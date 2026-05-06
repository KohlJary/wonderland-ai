# ADR-003: Reduce rate-limit collateral damage via multi-factor threshold

## Context

The credential-stuffing attack is halted by rate-limiting on source IP. But Alice's story about Marcus (shared corporate IP) reveals that simple IP-based rate-limiting will collateral-lock legitimate users alongside the attacker. The rate-limit is a blunt instrument: if the attacker and a legitimate user are on the same /24 subnet (or even the same /16 in a cloud environment), they both trigger the limit. The attack is stopped, but legitimate users are also stopped. This trades attacker damage for legitimate-user damage unless the unlock flow is frictionless (which ADR-001 addresses) *and* the rate-limit itself is tuned to minimize false positives (which ADR-001 does not address).

## Decision

The rate-limit threshold should be keyed on multiple factors, not IP alone. Proposed factorization: (IP, User-Agent, login-attempt-pattern). A single IP can have multiple User-Agents (different browsers, different devices); a single User-Agent can have multiple IPs (legitimate user moving networks). Rate-limiting that trips when a single IP + User-Agent combo exceeds 10 attempts in 5 minutes is higher-fidelity than IP-alone. Additionally, pattern-based detection (e.g., 'successful login from this IP + User-Agent, then 20 failed attempts in 2 minutes with different usernames') can be added as a secondary heuristic to distinguish attack-profile from user-error-profile. This is more complex than IP-keyed rate-limiting, but it reduces collateral damage to Marcus's cohort (legitimate users on shared corporate IPs).

## Tradeoffs

- Multi-factor rate-limiting is more complex to implement and reason about. IP-alone is simple; IP+UA is still tractable; IP+UA+pattern is getting expensive. Trade: complexity vs. false positives.
- Storing and checking (IP, User-Agent) tuples for every login attempt requires a higher-cardinality key space than IP-alone. Memory/cache efficiency is lower. For incident-response scale (hundreds of attempts/second), acceptable; may not scale to millions of users per hour.
- User-Agent headers are forgeable by the attacker (rotating User-Agent is cheap). Pattern-based heuristics are also forgeable (attacker can vary login attempt timing and patterns). Multi-factor rate-limiting is not a silver bullet — the attacker can still get in if sophisticated. But it raises the bar and reduces collateral damage to Marcus-like legitimate users, which is the acceptable tradeoff.
- Pattern-based detection requires baseline data (what does a normal login attempt look like? what does an attack look like?). The Dormouse's telemetry is needed to build these baselines. If baselines are wrong, false positives or false negatives spike. This is deferred to post-incident tuning, with the understanding that the first 48 hours will have higher collateral damage as baselines are learned.
- If we implement multi-factor rate-limiting now and switch to IP-only later (simpler, lower memory), we're adding and then removing complexity. But if we implement IP-only now and switch to multi-factor later (to fix Marcus's problem), we're adding complexity and accepting interim damage. It's cheaper to start with multi-factor if we know Marcus's problem exists now.

## Status

Proposed
